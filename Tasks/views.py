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

from StudentTasks.models import weeklytask
from .forms import TaskForm, SignUpForm, UserUpdateForm, YearPlanForm
from .models import Task, YearPlan
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

  #this is a supervisor deshbourd


@login_required
def supervisor_dashboard(request):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
    except Supervisor.DoesNotExist:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('home')

    # Get all students under this supervisor
    students = Student.objects.filter(supervisor=supervisor).select_related('user')
    
    # Calculate progress for each student
    for student in students:
        # Use student.user instead of student
        total_tasks = weeklytask.objects.filter(contract__student=student.user).count()
        completed_tasks = weeklytask.objects.filter(contract__student=student.user, status='Approved').count()
        student.progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Get USER IDs from students instead of student IDs
    student_user_ids = [student.user.id for student in students]
    
    # Update all queries to use contract__student_id__in with user IDs
    pending_tasks = weeklytask.objects.filter(
        contract__student_id__in=student_user_ids,
        status='Pending'
    ).select_related('contract', 'contract__student').order_by('-date')

    completed_tasks = weeklytask.objects.filter(
        contract__student_id__in=student_user_ids,
        status__in=['Approved', 'Rejected']
    ).select_related('contract', 'contract__student').order_by('-date')
    
    overdue_tasks = weeklytask.objects.filter(
        contract__student_id__in=student_user_ids,
        status='Pending',
        date__lt=timezone.now().date()
    ).select_related('contract', 'contract__student')

    all_tasks = weeklytask.objects.filter(
        contract__student_id__in=student_user_ids
    ).select_related('contract', 'contract__student')

    context = {
        'students': students,
        'tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'all_tasks': all_tasks,
        'pending_tasks': pending_tasks,
    }

    return render(request, 'Tasks/supervisor_dashboard.html', context)
    

 

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
        user = form.save(commit=False)  # Don't save immediately  
        user.username = form.cleaned_data['email']  # Set email as username  
        user.first_name = form.cleaned_data['first_name']  
        user.last_name = form.cleaned_data['last_name']  
        user.email = form.cleaned_data['email']  
        user.is_active = False  # Disable account until email verification  
        user.save()  # Now save with all fields  
        
      except IntegrityError:
        return render(request, 'Tasks/signupuser.html', {'form':SignUpForm(), 'error': 'Email already exists'})
        
        
      
      if sendActivationEmail(request, user):   
          messages.success(request, f"Activation email sent to {user.email} access you inbox to activate your account.")
      else:
          messages.error(request, "Somthing went wrong while sending activation email please contact support.")
          user.delete()  # Clean up if email fails
          return render(request, 'Tasks/signupuser.html', {'form': form,'error': 'Account creation failed - please try again'})
              
            #we send email
      return redirect('home')
    
    form= SignUpForm() 
  return render(request, 'Tasks/signupuser.html', {'form':SignUpForm(), 'error': 'please fix the errors and try again'})  ###this is causing the error
         
# Tasks/views.py




@login_required
def update_user(request, task_pk):
    user_instance = get_object_or_404(User, pk=task_pk)  # Fetch the user instance
    #form=UserUpdateForm()
    #if request.method =='GET':  
         #return redirect('update_user', task_pk=1)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user_instance)
        
        if form.is_valid():
            form.save()
            login(request, user_instance)
            messages.success(request,"your profile has been updated")
            return redirect('Mytasks')  # Redirect after successful update
    else:
      print("user_instance: ", user_instance.first_name)
      form = UserUpdateForm(instance=user_instance)  # Show form with user data
    
      # Add rendering for the form template
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
            #hasattr(user, 'supervisor'):
            # Redirect based on user type
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
            
            # Redirect to proper dashboard after password change
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
def Mytasks (request):
     student = getattr(request.user, 'student', None)
     tasks = Task.objects.filter( )
     #tasks=Task.objects.filter(user=request.user, datecomplited__isnull=True)
     search_input = request.GET.get('search-area') or ''
    
     if student:
        user_tasks = Task.objects.filter(assigned_to=request.user, datecomplited__isnull=True)
        student_tasks = Task.objects.filter(assigned_to_student=student, datecomplited__isnull=True)
        tasks = tasks | student_tasks 

        
     if search_input:
        tasks = tasks.filter(title__icontains=search_input)  

     context = {'tasks': tasks}
     return render(request, 'Tasks/MyTasks.html', context)

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
                task.full_clean()  # Explicit validation
                task.save()
                return redirect('task-list')
            except ValidationError as e:
                form.add_error(None, e)  # Add validation errors to form
        return render(request, 'tasks/createtask.html', {'form': form})
    else:
        form = TaskForm()
    return render(request, 'tasks/createtask.html', {'form': form})

@login_required
def viewtasks(request, task_pk):
  #users to view their list denie access to athor users 
  task= get_object_or_404(Task, pk=task_pk, user=request.user)
  if request.method == 'GET':
    form=  TaskForm( instance=task)
    return render(request, 'Tasks/viewtasks.html', {'task':task, 'form':form})
  else:
    try:
      form = TaskForm(request.POST, instance=task)
      form.save()
      return redirect('Mytasks') 
    except ValueError:
      return render(request,'Tasks/viewtasks.html', {'task':task, 'error':'band information'}, )
    
#allow the user to complet their tasks and it remive it from the task list  
@login_required
def completetasks(request, task_pk):
  student = get_object_or_404(Student, user=request.user)
  task= get_object_or_404(Task, pk=task_pk, student=student)
  if request.method == 'POST':

    task.datecomplited = timezone.now()
    task.status = "Completed"
    task.save()
    return redirect('StudentTasks:student_tasks_home')
  
 #allow the user to view their completed task show the completed date. 
@login_required
def completedtasks(request ):
  
  tasks=Task.objects.filter(user=request.user, datecomplited__isnull=False).order_by('-datecomplited')
     
  return render(request, 'Tasks/completedtasks.html', {'tasks':tasks})
  
@login_required  
def deletetasks(request, task_pk):
  task= get_object_or_404(Task, pk=task_pk, user=request.user)
  if request.method == 'POST':
    task.datecomplited = timezone.now()
    task.delete()
    return redirect('Mytasks')
  

@login_required
def supervisor_assign_task(request):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
    except Supervisor.DoesNotExist:
        messages.error(request, "You must be a supervisor to assign tasks.")
        return redirect('supervisor_dashboard')

    if request.method == 'POST':
        form = TaskForm(request.POST, supervisor=supervisor)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user  # the supervisor
            task.assigned_by = request.user
            task.save()
            messages.success(request, "Task assigned successfully.")
            return redirect('supervisor_dashboard')
    else:
        form = TaskForm(supervisor=supervisor)

    return render(request, 'Tasks/supervisor_assign_task.html', {'form': form})



  
@login_required
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES).keys():
            task.status = new_status
            if new_status == 'completed':
                task.completed_at = timezone.now()
            task.save()
            messages.success(request, 'Task status updated!')
    return redirect('Mytasks')
  
#supervisor create year plan for students
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

#students view their year plan here
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


  
  


          
        