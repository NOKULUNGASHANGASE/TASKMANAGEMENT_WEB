from datetime import timedelta
from django.forms import ValidationError
from django.shortcuts import render,redirect, reverse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm 
from django.contrib.auth.decorators import login_required
from StudentTasks.models import Contract, WeeklyReport
from .forms import StudentTaskForm, SignUpForm, UserUpdateForm, YearPlanForm,TaskForm, ReplyForm, MessageForm
from .models import Task, YearPlan, Message, StudentTask, Notification
from django.contrib import messages
from django.template.defaultfilters import date
from django.utils import timezone
from .emailing import *
from Tasks.google_calendar import create_task
from Tasks import emailing
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from Management.models import Student, Supervisor


def home(request):
 # messages.warning(request, "this is a test message")
  return render(request, 'Tasks/home.html')

  


@login_required
def supervisor_dashboard(request):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
    except Supervisor.DoesNotExist:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('home')

    # Get all students assigned to this supervisor
    students = Student.objects.filter(supervisor=supervisor).select_related('user')
    
    # Get student user IDs for task queries
    student_user_ids = [student.user.id for student in students]
    
    # Calculate student progress and get their contracts
    student_contracts = {}
    for student in students:
        try:
            contract = Contract.objects.get(student=student.user, supervisor=supervisor)
            student_contracts[student.user.id] = contract
            
            # Calculate progress based on submitted weeks
            total_weeks = ((contract.end_date - contract.start_date).days // 7) + 1
            submitted_weeks = WeeklyReport.objects.filter(
                contract=contract
            ).values_list('week_num', flat=True).distinct().count()
            
            student.progress_percentage = (submitted_weeks / total_weeks * 100) if total_weeks > 0 else 0
            student.total_weeks = total_weeks
            student.submitted_weeks = submitted_weeks
            student.contract = contract
            
        except Contract.DoesNotExist:
            student.progress_percentage = 0
            student.total_weeks = 0
            student.submitted_weeks = 0
            student.contract = None

    # Get various task lists
    pending_weekly_tasks = WeeklyReport.objects.filter(
        contract__student_id__in=student_user_ids,
        status='PENDING'
    ).select_related('contract', 'contract__student').order_by('-date')[:10]
    pending_weekly_tasks2 = getnumPending(supervisor.supervisorID)
    completed_weekly_tasks = WeeklyReport.objects.filter(
        contract__student_id__in=student_user_ids,
        status__in=['APPROVED', 'REJECTED']
    ).select_related('contract', 'contract__student').order_by('-date')[:10]

    overdue_weekly_tasks = WeeklyReport.objects.filter(
        contract__student_id__in=student_user_ids,
        status='PENDING',
        date__lt=timezone.now().date()
    ).select_related('contract', 'contract__student')

    # Get regular tasks (if you have a Task model)
    pending_regular_tasks = Task.objects.filter(
        student__in=students,
        status='PENDING'
    ).select_related('student', 'student__user').order_by('due_date')[:10]

    completed_regular_tasks = Task.objects.filter(
        student__in=students,
        status='COMPLETED'
    ).select_related('student', 'student__user').order_by('-due_date')[:10]

    overdue_regular_tasks = Task.objects.filter(
        student__in=students,
        status='PENDING',
        due_date__lt=timezone.now().date()
    ).select_related('student', 'student__user')

    # Count totals
    total_students = students.count()
    total_pending_weekly_tasks = WeeklyReport.objects.filter(
        contract__student_id__in=student_user_ids,
        status='PENDING'
    ).count()
    
    total_completed_weekly_tasks = WeeklyReport.objects.filter(
        contract__student_id__in=student_user_ids,
        status='APPROVED'
    ).count()
    
    total_overdue_weekly_tasks = overdue_weekly_tasks.count()

    # Recent activity
    recent_activity = []
    
    # Add weekly task submissions
    for task in pending_weekly_tasks:
        recent_activity.append({
            'type': 'weekly_submission', 
            'task': task, 
            'date': task.date, 
            'student': task.contract.student.get_full_name(),
            'week_num': task.week_num
        })
    
    # Add weekly task approvals/rejections
    for task in completed_weekly_tasks:
        recent_activity.append({
            'type': 'weekly_approval' if task.status == 'APPROVED' else 'weekly_rejection',
            'task': task,
            'date': task.date,
            'student': task.contract.student.get_full_name(),
            'week_num': task.week_num
        })
    
    # Add regular task completions
    for task in completed_regular_tasks[:5]:
        recent_activity.append({
            'type': 'task_completion',
            'task': task,
            'date': task.datecompleted.date() if task.datecompleted else timezone.now().date(),
            'student': task.student.user.get_full_name()
        })

    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    recent_activity = recent_activity[:10]

    # Students without any reports
    students_without_reports = 0
    for student in students:
        task_count = WeeklyReport.objects.filter(contract__student=student.user).count()
        if task_count == 0:
            students_without_reports += 1

    # Notifications
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-timestamp')[:10]

    # Messages
    messages_inbox = Message.objects.filter(
        recipient=request.user
    ).order_by('-timestamp')[:5]

    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    # Year plans for students
    year_plans = YearPlan.objects.filter(student__in=[student.user for student in students])[:5]

    context = {
        'supervisor': supervisor,
        'students': students,
        'student_contracts': student_contracts,
        
        # Weekly tasks
        'pending_weekly_tasks': pending_weekly_tasks,
        'completed_weekly_tasks': completed_weekly_tasks,
        'overdue_weekly_tasks': overdue_weekly_tasks,
        'pending_weekly_tasks2': pending_weekly_tasks2,
        # Regular tasks
        'pending_regular_tasks': pending_regular_tasks,
        'completed_regular_tasks': completed_regular_tasks,
        'overdue_regular_tasks': overdue_regular_tasks,
        
        # Notifications and messages
        'notifications': notifications,
        'messages_inbox': messages_inbox,
        'search_query': search_query,
        
        # Statistics
        'total_students': total_students,
        'total_pending_weekly_tasks': total_pending_weekly_tasks,
        'total_completed_weekly_tasks': total_completed_weekly_tasks,
        'total_overdue_weekly_tasks': total_overdue_weekly_tasks,
        
        # Activity and reports
        'recent_activity': recent_activity,
        'students_without_reports': students_without_reports,
        'year_plans': year_plans,
    }

    return render(request, 'Tasks/supervisor_dashboard.html', context)

def getnumPending(superVSId):

    supervisor = get_object_or_404(Supervisor, pk = superVSId)

    students = Student.objects.filter(supervisor= supervisor)

    report =[]
    TotalNumPending = 0
    

    for stud in students:
        studentContract = get_object_or_404(Contract, student =stud.user)

        studentWeekReports = WeeklyReport.objects.filter(contract= studentContract,status = "PENDING")
        TotalNumPending += studentWeekReports.count()

        report.append({
            "student": stud,
            "Contract": studentContract,
            "WeekTasks": studentWeekReports  
        })

    return { "TotalNumPending":TotalNumPending,"tasks": report }

 

def signupuser(request):
  
  form=SignUpForm()  
  
  payload = {
      "form":form       
    } 
  if request.method =='GET':  
    return render(request, 'Tasks/signupuser.html', payload) 
  
  if request.method == 'POST':           
    form= SignUpForm(request.POST)
    if form.is_valid():              
      email=form.cleaned_data['email'].lower()
      password1= form.cleaned_data['password1']
      password2= form.cleaned_data['password2']
    
      if password1 != password2:
        return render(request, 'Tasks/signupuser.html', {'form': form,'error': 'Passwords did not match'})
      
      try:
       if form.is_valid():  
        user = form.save(commit=False)   
        user.username = form.cleaned_data['email']    
        user.first_name = form.cleaned_data['first_name']  
        user.last_name = form.cleaned_data['last_name']  
        user.email = form.cleaned_data['email']  
        user.is_active = False    
        user.save()    
        
      except IntegrityError:
        return render(request, 'Tasks/signupuser.html', {'form':SignUpForm(), 'error': 'Email already exists'})
        
        
      
      if sendActivationEmail(request, user):   
          messages.success(request, f"Activation email sent to {user.email} access you inbox to activate your account.")
      else:
          messages.error(request, "Somthing went wrong while sending activation email please contact support.")
          user.delete()  
          return render(request, 'Tasks/signupuser.html', {'form': form,'error': 'Account creation failed - please try again'})
              
           
      return redirect('home')
    
    form= SignUpForm() 
  return render(request, 'Tasks/signupuser.html', {'form':SignUpForm(), 'error': 'please fix the errors and try again'})  ###this is causing the error
         





@login_required
def update_user(request, task_pk):
    user_instance = get_object_or_404(User, pk=task_pk)  
    
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user_instance)
        
        if form.is_valid():
            form.save()
            login(request, user_instance)
            messages.success(request,"your profile has been updated")
            return redirect('Mytasks')  
    else:
      print("user_instance: ", user_instance.first_name)
      form = UserUpdateForm(instance=user_instance)  
    
      
      return render(request, 'Tasks/updateuser.html', {'form': form})
    
@login_required
def PasswordChange(request):
    if request.method == "POST":
        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "Password changed successfully.")
            return redirect("update_user")
    return render(request, "Tasks/passwordChange.html")
  
  

        
def loginuser(request):
    if request.method == 'GET':
        return render(request, 'Tasks/Loginuser.html', {'form': AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'Tasks/Loginuser.html', {'form': AuthenticationForm(), 'error': 'user and password did not match'})
        else:
            try:
                if hasattr(user, 'supervisor') and user.supervisor.initial_password:
                    if user.supervisor.initial_password == request.POST['password']:
                        request.session['temp_user_id'] = user.id
                        messages.warning(request, "Please change your initial password")
                        return redirect('initial_password_change')
            except Supervisor.DoesNotExist:
                pass
            
            login(request, user)
            
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                try:
                    superviser = get_object_or_404(Supervisor,user = user )

                
                    return redirect('supervisor_dashboard')
                except:
                    try:
                        student =get_object_or_404(Student,user = user )
                        print("To redirect")
                        return redirect('StudentTasks:student_tasks_home')
                    except:
                       return redirect('home')
            

    
def initial_password_change(request):
    if 'temp_user_id' not in request.session:
        return redirect('loginuser')
    
    user_id = request.session['temp_user_id']
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('loginuser')
    
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            try:
                supervisor = Supervisor.objects.get(user=user)
                supervisor.initial_password = None
                supervisor.save()
            except Supervisor.DoesNotExist:
                pass
            
            update_session_auth_hash(request, user)
            login(request, user)
            del request.session['temp_user_id']
            
           
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif hasattr(user, 'supervisor'):
                return redirect('supervisor_dashboard')
            elif hasattr(user, 'student'):
                return redirect('student_tasks_home')
            else:
                return redirect('home')
    else:
        form = PasswordChangeForm(user)
    
    return render(request, 'Tasks/initial_password_change.html', {'form': form})


def logoutuser(request):
    if request.method == 'POST':
      logout(request)
      return redirect('home') 

  
@login_required  
def student_task_list(request):
   
    student = get_object_or_404(Student, user=request.user)
    tasks = StudentTask.objects.filter(student=student)

    return render(request, 'Tasks/MyTasks.html', {'tasks': tasks})

@login_required
def complete_task(request, task_id):
    
    student = get_object_or_404(Student, user=request.user)
    student_task = get_object_or_404(StudentTask, id=task_id, student=student)

    if request.method == 'POST':
        student_task.completed = True
        student_task.completed_date = timezone.now()
        student_task.save()
        messages.success(request, f"Task '{student_task.task.title}' marked as completed.")
        return redirect('student_task_list')

    return render(request, 'Tasks/viewtasks.html', {'task': student_task})

@login_required
def student_overdue_tasks(request):
  
    student = get_object_or_404(Student, user=request.user)
    overdue_tasks = [t for t in StudentTask.objects.filter(student=student) if t.is_overdue]

    return render(request, 'student_overdue_tasks.html', {'tasks': overdue_tasks})
@login_required
def createtask(request):
    if not request.user.is_supervisor:
        return redirect('not_allowed')
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            try:
                task.full_clean()  
                task.save()
                return redirect('task-list')
            except ValidationError as e:
                form.add_error(None, e)  
        return render(request, 'Tasks/createtask.html', {'form': form})
    else:
        form = TaskForm()
    return render(request, 'Tasks/createtask.html', {'form': form})


@login_required
def assign_task_to_student(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    supervisor = get_object_or_404(Supervisor, user=request.user)
    students = Student.objects.filter(supervisor=supervisor)

    if request.method == 'POST':
        form = StudentTaskForm(request.POST)
        if form.is_valid():
            student_task = form.save(commit=False)
            student_task.task = task
            student_task.save()
            messages.success(request, "Task assigned to student.")
            return redirect('supervisor_dashboard')
    else:
        form = StudentTaskForm()
        form.fields['student'].queryset = students

    return render(request, 'Task/assign_task_to_student.html', { 'form': form, 'task': task })

@login_required
def viewtasks(request, task_id):
  
  task= get_object_or_404(Task, id=task_id, user=request.user)
  if request.method == 'GET':
    form=  TaskForm( instance=task)
    return render(request, 'Tasks/viewtasks.html', {'task':task, 'form':form})
  else:
    try:
      form = TaskForm(request.POST, instance=task)
      form.save()
      return redirect('student_task_list') 
    except ValueError:
      return render(request,'Tasks/viewtasks.html', {'task':task, 'error':'bad information'}, )
    
    
@login_required
def create_year_plan(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if not Supervisor.objects.filter(user=request.user).exists():
        return redirect('not_allowed')
    
    student_id = request.GET.get('student_id')
    if student_id:
        student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        form = YearPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            supervisor = Supervisor.objects.get(user=request.user)
            plan.supervisor = supervisor.user
            plan.save()
            return redirect('supervisor_dashboard')  
    else:
        form = YearPlanForm()

        payload = {
           'form': form,
        }
    return render(request, 'Tasks/create_year_plan.html', payload)


@login_required
def view_year_plan(request):
    student = get_object_or_404(Student, user=request.user)
    plans = YearPlan.objects.filter(student=student.user)
    domain = get_current_site(request).domain
    protocol = 'https' if request.is_secure() else 'http'
    payload = {
        'domain': domain,
        'protocol': protocol,
        'plans': plans
    }
    return render(request, 'Tasks/year_plan_calendar.html',payload )
@login_required
def message_center(request):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
        
        # Get sent and received messages
        sent_messages = Message.objects.filter(sender=request.user).order_by('-timestamp')
        received_messages = Message.objects.filter(recipient=request.user).order_by('-timestamp')
        
        # Get students for composing new messages
        students = Student.objects.filter(supervisor=supervisor)
        
        if request.method == 'POST':
            form = MessageForm(request.POST)
            if form.is_valid():
                message = form.save(commit=False)
                message.sender = request.user
                
                # Verify the recipient is one of supervisor's students
                recipient_user = message.recipient
                try:
                    student = Student.objects.get(user=recipient_user)
                    if student.supervisor != supervisor:
                        messages.error(request, "You can only message your assigned students.")
                        return redirect('message_center')
                except Student.DoesNotExist:
                    messages.error(request, "Invalid recipient.")
                    return redirect('message_center')
                
                message.save()
                
                # Create notification for recipient
                Notification.objects.create(
                    recipient=message.recipient,
                    message=f"New message from {request.user.get_full_name()}: {message.subject}"
                )
                
                messages.success(request, "Message sent successfully.")
                return redirect('message_center')
        else:
            form = MessageForm()
        
        context = {
            'sent_messages': sent_messages,
            'received_messages': received_messages,
            'students': students,
            'form': form,
        }
        return render(request, 'StudentTasks/messagecenter.html', context)
        
    except Supervisor.DoesNotExist:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('home')

@login_required
def reply_message(request, message_id):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
        original_message = get_object_or_404(Message, id=message_id, recipient=request.user)
        
        if request.method == 'POST':
            form = ReplyForm(request.POST)
            if form.is_valid():
                reply = form.save(commit=False)
                reply.sender = request.user
                reply.recipient = original_message.sender
                reply.subject = f"Re: {original_message.subject}"
                reply.save()
                
                messages.success(request, "Reply sent successfully.")
                return redirect('message_center')
        else:
            form = ReplyForm(initial={'body': f"\n\n--- Original Message ---\nFrom: {original_message.sender.get_full_name()}\nSubject: {original_message.subject}\n\n{original_message.body}"})
        
        context = {
            'form': form,
            'original_message': original_message,
        }
        return render(request, 'StudentTasks/reply_message.html', context)
        
    except Supervisor.DoesNotExist:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('home')

  
  


          
        