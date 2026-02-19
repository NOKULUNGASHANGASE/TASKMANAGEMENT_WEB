from datetime import timezone
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from StudentTasks.models import Contract, WeeklyReport
from Tasks.models import ActivityLog, Task
from .forms import SupervisorCreationForm
from .models import Supervisor, Student
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone


@user_passes_test(lambda u: u.is_superuser)
def create_supervisor(request):
    if request.method == 'POST':
        form = SupervisorCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(username=email).exists():
                messages.error(request, "A user with this email already exists.")
                return render(request, 'Management/create_supervisor.html', {'form': form})
            
            user = form.save(commit=False)
            user.username = email
            user.save()
        

            
            
            supervisor = Supervisor.objects.create(
                user=user,
                status='active',
                initial_password=form.cleaned_data['password1']
            )
            
            
            ActivityLog.objects.create(
                user=request.user,
                action="Created supervisor",
                description=f"Created supervisor account for {user.email}"
            )
            
            students = form.cleaned_data['students']
            for student in students:
                student.supervisor = supervisor
                student.save()
            
           
            subject = 'Your Supervisor Account Credentials'
            message = f'''
            Hello {user.first_name},
            
            Your supervisor account has been created:
            
            Login URL: {settings.LOGIN_URL}
            Email: {user.email}
            Password: {form.cleaned_data['password1']}
            
            Please change your password after first login.
            '''
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Supervisor created and email sent!')
            return redirect('admin_dashboard')
    else:
        form = SupervisorCreationForm()
    
    return render(request, 'Management/create_supervisor.html', {'form': form})



@user_passes_test(lambda u: u.is_superuser)
def assign_students(request, supervisor_id):
    if request.method == 'POST':
        supervisor_id = request.POST.get('supervisor_id')
        student_ids = request.POST.getlist('students')

        if supervisor_id and student_ids:
            try:
                supervisor = Supervisor.objects.get(pk=supervisor_id)
            except Supervisor.DoesNotExist:
                messages.error(request, 'Selected supervisor does not exist.')
                return redirect('admin_dashboard')

            students = Student.objects.filter(id__in=student_ids)
            students.update(supervisor=supervisor)

            messages.success(request, f'{students.count()} students assigned to {supervisor.user.get_full_name()}')
        else:
            messages.error(request, 'Please select a supervisor and at least one student.')

    return redirect('admin_dashboard')



@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):

    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='active').count()
    inactive_students = Student.objects.filter(status='inactive').count()
    
    # Supervisor statistics
    total_supervisors = Supervisor.objects.count()
    active_supervisors = Supervisor.objects.filter(status='active').count()
    
    # Contract statistics
    total_contracts = Contract.objects.count()
    active_contracts = Contract.objects.filter(is_active=True).count()
    
    # Task statistics - FIXED
    total_tasks = Task.objects.count()
    completed_tasks_count = Task.objects.filter(date_completed__isnull=False).count()
    pending_tasks_count = Task.objects.filter(date_completed__isnull=True).count()
    overdue_tasks_count = Task.objects.filter(
    date_completed__isnull=True,
    due_date__lt=timezone.now()
    ).count()

    total_reports = WeeklyReport.objects.count()
    pending_reports = WeeklyReport.objects.filter(status='PENDING').count()
    approved_reports = WeeklyReport.objects.filter(status='APPROVED').count()
    rejected_reports = WeeklyReport.objects.filter(status='REJECTED').count()
    
    # Recent activities
    recent_students = Student.objects.all().order_by('-id')[:5]
    recent_supervisors = Supervisor.objects.all().order_by('-supervisorID')[:5]
    recent_tasks = Task.objects.all().order_by('-created')[:10]
    recent_reports = WeeklyReport.objects.all().order_by('-date')[:10]
    
    context = {
        # Student stats
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        
        # Supervisor stats
        'total_supervisors': total_supervisors,
        'active_supervisors': active_supervisors,
        
        # Contract stats
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,

        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks_count,
        'pending_tasks': pending_tasks_count,
        'overdue_tasks': overdue_tasks_count,
        
        # Report stats
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'approved_reports': approved_reports,
        'rejected_reports': rejected_reports,
        
        # Recent items
        'recent_students': recent_students,
        'recent_supervisors': recent_supervisors,
        'recent_tasks': recent_tasks,
        'recent_reports': recent_reports,
    }

    
    return render(request, 'Management/admin_dashboard.html', context)

