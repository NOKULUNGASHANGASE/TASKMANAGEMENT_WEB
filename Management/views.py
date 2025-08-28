from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from StudentTasks.models import weeklytask
from Tasks.models import ActivityLog, Task
from .forms import SupervisorCreationForm
from .models import Supervisor, Student
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

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
        

            
            # Create supervisor
            supervisor = Supervisor.objects.create(
                user=user,
                status='active',
                initial_password=form.cleaned_data['password1']
            )
            
            # Example in create_supervisor view
            ActivityLog.objects.create(
                user=request.user,
                action="Created supervisor",
                description=f"Created supervisor account for {user.email}"
            )
            # Assign students
            students = form.cleaned_data['students']
            for student in students:
                student.supervisor = supervisor
                student.save()
            
            # Send email with credentials
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
    supervisors = Supervisor.objects.all().select_related('user')
    students = Student.objects.all().select_related('user', 'supervisor')
    active_supervisors = supervisors.filter(status='active')
    unassigned_students = Student.objects.filter(supervisor=None)
    completed_tasks_count = weeklytask.objects.filter(status='Approved').count()
    # Get completed tasks count (adjust based on your Task model)
    completed_tasks_count = Task.objects.filter(status='completed').count()
    
    # Recent activities (you might need an ActivityLog model)
    recent_activities = ActivityLog.objects.all().order_by('-timestamp')[:5]
    activity_list = [
        {
            "description": f"{task.contract.student.user.get_full_name()} submitted task for Week {task.week_num}",
            "timestamp": task.date,
        }
        for task in recent_activities
    ]
    context = {
        'supervisors': supervisors,
        'active_supervisors': active_supervisors,
        'students': students,
        'unassigned_students': unassigned_students,
        'total_students': students.count(),
        'completed_tasks_count': completed_tasks_count,
        'active_supervisors': supervisors,
        'recent_activities': activity_list,
    }
    return render(request, 'Management/admin_dashboard.html', context)

