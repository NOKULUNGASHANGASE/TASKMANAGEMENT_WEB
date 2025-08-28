from django.views import generic
from django.shortcuts import render,redirect, reverse
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db import IntegrityError
from django.contrib import messages
from django.template.defaultfilters import date
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from StudentTasks.emailing import send_task_email
from .models import Contract, weeklytask
from .forms import ContractForm, weeklytaskForm
from datetime import timedelta
from django.core.mail import send_mail
from collections import defaultdict
from django.core.exceptions import PermissionDenied
from Management.models import Student, Supervisor
from Tasks.models import Task, YearPlan
from django.views.decorators.http import require_POST
import datetime
import json
from django.conf import settings
from StudentTasks import emailing



@login_required
def student_tasks_home(request):
    contract = Contract.objects.filter(student=request.user).first()
    student = get_object_or_404(Student, user=request.user)
    # student = Student.objects.get(user=request.user)
    if not contract:
        return render(request, 'StudentTasks/home.html')

    today = timezone.now().date()
    total_weeks = ((contract.end_date - contract.start_date).days // 7) + 1

    # All submitted week numbers for this contract
    #submitted_week_nums = weeklytask.objects.filter(contract=contract).values_list('week_num', flat=True)
    submitted_week_nums = set(
        weeklytask.objects.filter(contract=contract)
        .values_list('week_num', flat=True)
    )

    # Calculate progress based on weeks submitted
    submitted_weeks_count = len(set(submitted_week_nums))
    submission_progress = (submitted_weeks_count / total_weeks) * 100 if total_weeks > 0 else 0

    # Find overdue weeks with no submission for the student
    overdue_weeks = []
    for week_num in range(1, total_weeks + 1):
        week_start = contract.start_date + timedelta(days=(week_num - 1) * 7)
        week_end = week_start + timedelta(days=6)

        # If week has ended and no task submitted
        if week_end < today and week_num not in submitted_week_nums:
            overdue_weeks.append({
                'week_num': week_num,
                'start_date': week_start,
                'end_date': week_end
            })
    #last updated task  
    last_task = weeklytask.objects.filter(contract=contract).order_by('-date').first()    
    #list of tasks assigned to student not yet completed
    due_tasks = Task.objects.filter(
        student=student,
        datecomplited__isnull=True,
        due_date__lte=timezone.now().date()
    ).order_by('due_date')
    all_tasks = Task.objects.filter(student=student).order_by('-due_date')


     # Completed tasks
    completed_tasks = Task.objects.filter(
        student=student,
        datecomplited__isnull=False
    ).order_by('-datecomplited')
    #year plan calender
    plans = YearPlan.objects.filter(student=request.user)
    
    week_labels = []
    expected_submissions = []
    actual_submissions = []
    week_labels = [f"Week {i}" for i in range(1, total_weeks + 1)]
    for week_num in range(1, total_weeks + 1):
        expected_submissions.append(1)
        actual_submissions.append(1 if week_num in submitted_week_nums else 0)
    #calender events
    events = [{
        'title': task.title,
        'start': task.due_date.isoformat(),
        'end': (task.due_date + timedelta(days=1)).isoformat(),
        'is_overdue': task.due_date.date() < today and task.datecomplited is None,
        'status': task.status,
        'task_id': task.id,
        'className': 'task-overdue' if task.due_date.date() < today and task.datecomplited is None else 'task-due'
    } for task in due_tasks]

    
        

    context = {
        'contract': contract,
        'contract_id': contract.id,
        'submission_progress': round(submission_progress),
        'total_weeks': total_weeks,
        'submitted_weeks': submitted_weeks_count,
        'overdue_weeks': overdue_weeks,
        'last_task': last_task,
        'all_tasks': all_tasks,
        'completed_tasks': completed_tasks,
        'due_tasks': due_tasks,
        'events': events,
        'week_labels': week_labels,
        'expected_submissions': expected_submissions,
        'actual_submissions': actual_submissions,
        'plans':plans
        
    }
    return render(request, 'StudentTasks/home.html', context)




@login_required
def contract_list(request):
    contract = Contract.objects.filter(student=request.user)
    return render(request, 'StudentTasks/contract_list.html', {'contract': contract})


@login_required
def contract_create(request):
    if Contract.objects.filter(student=request.user).exists():
        messages.info(request, "you already have a contract.")
        return redirect('student_tasks_home')
    
    
    if request.method == 'POST':
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = form.save(commit=False)
             
            contract.student = request.user

            contract.save()
            contract.generate_time_periods()
            messages.success(request, "Contract created and tasks generated.")
            return redirect('StudentTasks:contract_list')
    else:
        form = ContractForm()
    return render(request, 'StudentTasks/contract.html', {'form': form })

@login_required
def contract_detail(request,  contract_id):
    contract = get_object_or_404(Contract,  id=contract_id, student=request.user)
    return render(request, 'StudentTasks/contract_detail.html', {'contract': contract})


@login_required
def weeklytask_list(request, contract_id):
    #contract = get_object_or_404(Contract, id=contract_id, student=request.user)
    #tasks = WeeklyTask.objects.filter(contract_id=contract_id)
    contract = get_object_or_404(Contract, id=contract_id)
    tasks = weeklytask.objects.filter(contract=contract).order_by('week_num')
    context = {
        'contract': contract,  
        'tasks': tasks,
    }
    
    return render(request, 'StudentTasks/weeklytask_list.html', context)

@login_required
def weeklytask_create(request, contract_id):
    user_contracts = Contract.objects.filter(student=request.user)
    
    if user_contracts.count() != 1:
        messages.warning(request, "You must have exactly one active contract to add weekly tasks.")
        return redirect('StudentTasks:contract_list')

    contract = get_object_or_404(Contract, id=contract_id, student=request.user)
    if contract != user_contracts.first():
        raise PermissionDenied("You can only add tasks to your own single contract.")
    if request.method == "POST":
        form = weeklytaskForm(request.POST, contract=contract)
        if form.is_valid():
            tasks = form.save(commit=False)
            # Enforce task contract
            tasks.contract = contract
            tasks.week_num = form.cleaned_data['week_num']
            if not tasks.hours_spent:
                tasks.hours_spent = tasks.expected_hours()
            tasks.save()

            # Extra validation: task date must not be before contract start
            if tasks.date < contract.start_date:
                form.add_error('date', "Task date cannot be before contract start date.")
            elif tasks.date > timezone.now().date():
                form.add_error('date', "Cannot add tasks for future dates.")
            else:
                tasks.save()
                messages.success(request, "Weekly task created successfully.")
                return redirect('StudentTasks:weeklytask_list', contract_id=contract.id)
    else:
        form = weeklytaskForm()

    return render(request, 'StudentTasks/weeklytask_form.html', {'form': form, 'contract': contract, 'default_hours': 40-(0*8)})  

@require_POST
@login_required
def approve_weeklytask(request, task_id):
    task = get_object_or_404(weeklytask, pk=task_id)
    if request.user != task.contract.student.supervisor.user:
        messages.error(request, "You are not authorized to approve this task.")
        return redirect('Tasks:supervisor_dashboard')

    task.status = 'Approved'
    task.save()

    # Send email notification
    subject = "Your Weekly Task Has Been Approved"
    message = f"Hi {task.contract.student.user.get_full_name()},\n\nYour weekly task for Week {task.week_num} has been approved by your supervisor."
    send_task_email(task, subject, message)

    messages.success(request, "Task approved and email sent to student.")
    return redirect('Tasks:supervisor_dashboard')

@require_POST
@login_required
def reject_weeklytask(request, task_id):
    task = get_object_or_404(weeklytask, pk=task_id)
    if request.user != task.contract.student.supervisor.user:
        messages.error(request, "You are not authorized to reject this task.")
        return redirect('Tasks:supervisor_dashboard')

    task.status = 'Rejected'
    task.save()

    # Send email notification to student after the supervisor aprouve or reject
    subject = "Your Weekly Task Has Been Rejected"
    message = f"Hi {task.contract.student.user.get_full_name()},\n\nYour weekly task for Week {task.week_num} has been rejected by your supervisor.\nPlease review and resubmit."
    send_task_email(task, subject, message)

    messages.warning(request, "Task rejected and email sent to student.")
    return redirect('Tasks:supervisor_dashboard')

