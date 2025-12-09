from mailbox import Message
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
from .models import Contract, WeeklyReport
from .forms import ContractForm, WeeklyReportForm
from datetime import timedelta
from django.core.mail import send_mail
from collections import defaultdict
from django.core.exceptions import PermissionDenied
from Management.models import Student, Supervisor
from Tasks.models import StudentTask, Task, YearPlan,Message, Notification
from django.views.decorators.http import require_POST
import datetime
import json
from django.conf import settings
from StudentTasks import emailing




@login_required
def student_tasks_home(request):
    student = get_object_or_404(Student, user=request.user)
    contract = Contract.objects.filter(student=student).first()

    if not contract:
        return render(request, 'StudentTasks/home.html')

    today = timezone.now().date()
    total_weeks = ((contract.end_date - contract.start_date).days // 7) + 1

    # FIXED: use student not contract
    submitted_week_nums = set(
        WeeklyReport.objects.filter(student=student)
        .values_list('week_num', flat=True)
    )

    submitted_weeks_count = len(submitted_week_nums)
    submission_progress = (submitted_weeks_count / total_weeks) * 100 if total_weeks > 0 else 0

    overdue_weeks = []
    for week_num in range(1, total_weeks + 1):
        week_start = contract.start_date + timedelta(days=(week_num - 1) * 7)
        week_end = week_start + timedelta(days=6)

        if week_end < today and week_num not in submitted_week_nums:
            overdue_weeks.append({
                'week_num': week_num,
                'start_date': week_start,
                'end_date': week_end
            })

  
    last_task = WeeklyReport.objects.filter(student=student).order_by('-date').first()

  
    due_tasks = StudentTask.objects.filter(
        student=student,
        date_completed__isnull=True,
        due_date__lte=timezone.now()
    ).order_by('due_date')

   
    all_tasks = StudentTask.objects.filter(student=student).order_by('-due_date')


    completed_tasks = StudentTask.objects.filter(
        student=student,
        date_completed__isnull=False
    ).order_by('-date_completed')

    plans = YearPlan.objects.filter(student=request.user)

    week_labels = [f"Week {i}" for i in range(1, total_weeks + 1)]
    expected_submissions = [1] * total_weeks
    actual_submissions = [1 if week in submitted_week_nums else 0 for week in range(1, total_weeks + 1)]

    events = [{
        'title': task.title,
        'start': task.due_date.isoformat(),
        'end': (task.due_date + timedelta(days=1)).isoformat(),
        'is_overdue': task.due_date < today and task.date_completed is None,
        'status': task.status,
        'task_id': task.id,
        'className': 'task-overdue' if task.due_date < today and task.date_completed is None else 'task-due'
    } for task in due_tasks]

    completed_percent = (submitted_weeks_count / total_weeks) * 100 if total_weeks > 0 else 0
    overdue_count = len(overdue_weeks)
    overdue_percent = (overdue_count / total_weeks) * 100 if total_weeks > 0 else 0
    pending_percent = 100 - completed_percent - overdue_percent

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
        'plans': plans,
        'completed_percent': round(completed_percent),
        'overdue_percent': round(overdue_percent),
        'pending_percent': round(pending_percent),
    }
    return render(request, 'StudentTasks/home.html', context)





@login_required
def contract_list(request):

    student = get_object_or_404(Student, user=request.user)
    
  
    if student.contract:
        contracts = [student.contract]
    else:
        contracts = []
    
    return render(request, 'StudentTasks/contract_list.html', {'contract':contracts})


@login_required
def contract_create(request):
    student = get_object_or_404(Student, user=request.user)

    if student.contract:
        messages.info(request, "you already have a contract.")
        return redirect('StudentTasks:student_tasks_home')
    
    
    if request.method == 'POST':
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = form.save()
            student.contract = contract
            student.save()

            contract.generate_time_periods()
            messages.success(request, "Contract created and tasks generated.")
            return redirect('StudentTasks:contract_list')
    else:
        form = ContractForm()
    return render(request, 'StudentTasks/contract.html', {'form': form })


@login_required
def contract_update(request, pk):
    student = get_object_or_404(Student, user=request.user)
    contract = get_object_or_404(Contract, pk=pk, student=student)

    if student.contract != contract:
        messages.error(request, "You are not authorized to update this contract.")
        return redirect('StudentTasks:contract_list')
    
    
    if request.method == 'POST':
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, "Contract updated successfully.")
            return redirect('StudentTasks:contract_list')
    else:
        form = ContractForm(instance=contract)

    return render(request, 'StudentTasks/contract.html', {'form': form})


@login_required
def contract_delete(request, pk):
    student = get_object_or_404(Student, user=request.user)
    contract = get_object_or_404(Contract, pk=pk)


    if student.contract != contract:
        messages.error(" You are not authorized to delete this contract please cont the admin for more information")
        return redirect('StudentTasks:contract_list')
    
    if request.method == 'POST':
        student.contract = None
        student.save()
        contract.delete()
        messages.success(request, "Contract deleted successfully.")
        return redirect('StudentTasks:contract_list')

    return render(request, 'StudentTasks/contract_confirm_delete.html', {'contract': contract})

@login_required
def contract_detail(request, pk):
    #collect contract object
    contract = get_object_or_404(Contract, pk=pk)

    #verify the contract belong to the logged in student
    student = get_object_or_404(Student, user=request.user)
    if student.contract != contract:
        messages.error(request, "You are not authorized to view this contract.")
        return redirect('StudentTasks:contract_list')

    weekly_reports = contract.weekly_reports.all()

    return render(request, 'Contracts/contract_detail.html', {'contract': contract,'weekly_reports': weekly_reports, })

@login_required
def create_weekly_report(request):
    """Allow students to submit their weekly reports."""
    student = get_object_or_404(Student, user=request.user)
    active_contract = Contract.objects.filter(start_date__lte=timezone.now().date(), end_date__gte=timezone.now().date()).first()

    if not active_contract:
        messages.warning(request, "You don't have an active contract to report for.")
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = WeeklyReportForm(request.POST, student=student, contract=active_contract)
        if form.is_valid():
            report = form.save(commit=False)
            report.student = student
            report.contract = active_contract
            report.status = 'PENDING'
            report.save()
            messages.success(request, f"Weekly report for Week {report.week_num} submitted successfully.")
            return redirect('my_weekly_reports')
    else:
        form = WeeklyReportForm(student=student, contract=active_contract)

    return render(request, 'StudentTasks/weeklytask_form.html', {'form': form})


@login_required
def my_weekly_reports(request):
    student = get_object_or_404(Student, user=request.user)
    reports = WeeklyReport.objects.filter(student=student).order_by('-week_num')
    return render(request, 'StudentTasks/weeklytask_list.html', {'reports': reports})

@login_required
def review_weekly_reports(request):
    supervisor = get_object_or_404(Supervisor, user=request.user)
    reports = WeeklyReport.objects.filter(student__supervisor=supervisor).select_related('student', 'contract').order_by('contract', 'week_num')
    return render(request, 'StudentTasks/review_reports.html', {'reports': reports})

@require_POST
@login_required
def approve_weeklyreport(request, report_id):
    report = get_object_or_404(WeeklyReport, pk=report_id)
    supervisor = get_object_or_404(Supervisor, user=request.user)

    if report.student.supervisor != supervisor:
        messages.error(request, "You are not authorized to approve this report.")
        return redirect('supervisor_dashboard')

    report.status = 'APPROVED'
    report.save()
    messages.success(request, "Report approved successfully.")
    return redirect('supervisor_dashboard')


@require_POST
@login_required
def reject_weeklyreport(request, report_id):
    report = get_object_or_404(WeeklyReport, pk=report_id)
    supervisor = get_object_or_404(Supervisor, user=request.user)

    if report.student.supervisor != supervisor:
        messages.error(request, "You are not authorized to reject this report.")
        return redirect('supervisor_dashboard')

    report.status = 'REJECTED'
    report.save()
    messages.warning(request, "Report rejected.")
    return redirect('supervisor_dashboard')
 
