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
from django.db.models import Q, Count
import datetime
import json
from django.conf import settings
from StudentTasks import emailing
import uuid




@login_required
def student_tasks_home(request):
    student = get_object_or_404(Student, user=request.user)
    contract = Contract.objects.filter(student=student).first()

    contract_stats = {}
    if contract:
        total_weeks = ((contract.end_date - contract.start_date).days // 7) + 1
        
        submitted_reports = WeeklyReport.objects.filter(student=student).count()
        approved_reports = WeeklyReport.objects.filter(student=student, status='APPROVED').count()
    
        contract_stats = {
            'total_weeks': total_weeks,
            'submitted_reports': submitted_reports,
            'approved_reports': approved_reports,
            'progress_percentage': contract.progress_percent(),
            'weeks_completed': contract.weeks_completed,
            'weeks_remaining': contract.weeks_remaining,
            'days_remaining': (contract.end_date - timezone.now().date()).days,
            'total_hours_logged': contract.total_w_hours(),
            'expected_hours': contract.total_day_hours(),
        }
    
    recent_report = WeeklyReport.objects.filter(student=student).order_by('-week_num')[:5]
    
    pending_report = WeeklyReport.objects.filter(student=student, status='PENDING').count()
    
    rejected_reports = WeeklyReport.objects.filter(student=student, status='REJECTED').order_by('-week_num')[:5]
    
    
    pending_tasks = StudentTask.objects.filter(
        student=student, 
        completed=False
    ).select_related('task').order_by('due_date')[:10]
    
   
    completed_tasks = StudentTask.objects.filter(
        student=student, 
        completed=True
    ).select_related('task').order_by('-date_completed')[:5]

    overdue_tasks = StudentTask.objects.filter(
        student=student, 
        completed=False,
        due_date__lt=timezone.now()
    ).select_related('task').order_by('due_date')
    
    
    due_tasks = StudentTask.objects.filter(
        student=student, 
        date_completed__isnull=True, 
        due_date__lte=timezone.now()
    ).order_by('due_date')
   
    total_tasks = StudentTask.objects.filter(student=student).count()
    total_completed = StudentTask.objects.filter(student=student, completed=True).count()
    total_pending = StudentTask.objects.filter(student=student, completed=False).count()
    total_overdue = overdue_tasks.count()
    


    if contract:
        today = timezone.now().date()
        total_weeks = ((contract.end_date - contract.start_date).days // 7) + 1

        submitted_week_nums = set(WeeklyReport.objects.filter(student=student).values_list('week_num', flat=True))

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

        week_labels = [f"Week {i}" for i in range(1, total_weeks + 1)]
        expected_submissions = [1] * total_weeks
        actual_submissions = [1 if week in submitted_week_nums else 0 for week in range(1, total_weeks + 1)]
        
        completed_percent = (submitted_weeks_count / total_weeks) * 100 if total_weeks > 0 else 0
        overdue_count = len(overdue_weeks)
        overdue_percent = (overdue_count / total_weeks) * 100 if total_weeks > 0 else 0
        pending_percent = 100 - completed_percent - overdue_percent
    else:
        
        total_weeks = 0
        submitted_week_nums = set()
        submitted_weeks_count = 0
        submission_progress = 0
        overdue_weeks = []
        week_labels = []
        expected_submissions = []
        actual_submissions = []
        completed_percent = 0
        overdue_percent = 0
        pending_percent = 0

    last_task = WeeklyReport.objects.filter(student=student).order_by('-date').first()
    all_tasks = StudentTask.objects.filter(student=student).order_by('-due_date')
    plans = YearPlan.objects.filter(student=request.user)

    year_plans = YearPlan.objects.filter(student=student.user).order_by('-start_date')[:5]
    
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-timestamp')[:10]
    unread_notifications_count = notifications.count()
    
    recent_messages = Message.objects.filter(recipient=request.user).order_by('-timestamp')[:5]
    unread_messages_count = Message.objects.filter(recipient=request.user, is_read=False).count() if hasattr(Message, 'is_read') else 0
    
    recent_activity = []
    
    for report in recent_report[:3]:
        recent_activity.append({
            'type': 'report_submission',
            'report': report,
            'date': report.date,
            'status': report.status,
            'description': f"Week {report.week_num}: {report.title}"
        })
    
    for task in completed_tasks[:3]:
        recent_activity.append({
            'type': 'task_completion',
            'task': task,
            'date': task.date_completed if task.date_completed else timezone.now(),
            'description': task.task.title
        })
    
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    recent_activity = recent_activity[:10]
    
    upcoming_deadlines = []
    
    for task in pending_tasks[:5]:
        if task.due_date > timezone.now():
            upcoming_deadlines.append({
                'type': 'task',
                'title': task.task.title,
                'due_date': task.due_date,
                'days_until': (task.due_date.date() - timezone.now().date()).days
            })
    
    if contract and contract.end_date > timezone.now().date():
        upcoming_deadlines.append({
            'type': 'contract',
            'title': 'Contract End Date',
            'due_date': contract.end_date,
            'days_until': (contract.end_date - timezone.now().date()).days
        })
    
    upcoming_deadlines.sort(key=lambda x: x['due_date'])
    upcoming_deadlines = upcoming_deadlines[:5]
    
    has_supervisor = student.supervisor is not None
    
    needs_weekly_report = False
    if contract:
        valid_weeks = [choice[0] for choice in contract.get_week_choices()]
        if valid_weeks:
            current_week = valid_weeks[-1]
            # Remove contract filter
            report_exists = WeeklyReport.objects.filter(student=student, week_num=current_week).exists()
            needs_weekly_report = not report_exists

    # Add contract check before creating events
    if contract:
        today = timezone.now().date()
        events = [{
            'title': task.title,
            'start': task.due_date.isoformat(),
            'end': (task.due_date + timedelta(days=1)).isoformat(),
            'is_overdue': task.due_date < today and task.date_completed is None,
            'status': task.status,
            'task_id': task.id,
            'className': 'task-overdue' if task.due_date < today and task.date_completed is None else 'task-due'
        } for task in due_tasks]
    else:
        events = []

    context = {
        'contract': contract,
        'contract_id': contract.id if contract else None,
        'student': student,
        'contract_stats': contract_stats,
        'has_supervisor': has_supervisor,

        'recent_reports': recent_report,
        'pending_reports_count': pending_report,
        'rejected_reports': rejected_reports,
        'needs_weekly_report': needs_weekly_report,

        'submission_progress': round(submission_progress),
        'total_weeks': total_weeks,
        'submitted_weeks': submitted_weeks_count,
        'overdue_weeks': overdue_weeks,
        'last_task': last_task,
        'all_tasks': all_tasks,
        'completed_tasks': completed_tasks,
        'due_tasks': due_tasks,

        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'total_tasks': total_tasks,
        'total_completed_tasks': total_completed,
        'total_pending_tasks': total_pending,
        'total_overdue_tasks': total_overdue,

        'events': events,
        'week_labels': week_labels,
        'expected_submissions': expected_submissions,
        'actual_submissions': actual_submissions,

        'year_plans': year_plans,
        'plans': plans,

        'completed_percent': round(completed_percent),
        'overdue_percent': round(overdue_percent),
        'pending_percent': round(pending_percent),

        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'recent_messages': recent_messages,
        'unread_messages_count': unread_messages_count,

        'recent_activity': recent_activity,
        'upcoming_deadlines': upcoming_deadlines,
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
            contract.contract_id = f"CTR-{uuid.uuid4().hex[:8].upper()}"
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
    student = get_object_or_404(Student, user=request.user)

    if student.contract != contract:
        messages.error(request, "You are not authorized to view this contract.")
        return redirect('StudentTasks:contract_list')
    
    context ={
        'contract' : contract,
        'weekly_reports' : contract.weekly_reports.all(),
        'weeks_completed ': contract.weeks_completed,
        'weeks_remaining' : contract.weeks_remaining,
    }
    return render(request, 'Contracts/contract_detail.html', context)

@login_required
def create_weekly_report(request):
  
    student = get_object_or_404(Student, user=request.user)
    active_contract = Contract.objects.filter(start_date__lte=timezone.now().date(), end_date__gte=timezone.now().date()).first()

    if not active_contract:
        messages.warning(request, "You don't have an active contract to report for.")
        return redirect('contract_create')
    
    if not student.supervisor:
        messages.error(request, " No supervisor assigned to you yet contact the admin support.")
        return redirect('StudentTasks:student_tasks_home')

    if request.method == 'POST':
        form = WeeklyReportForm(request.POST, student=student, contract=active_contract)
        
        if form.is_valid():
            report = form.save(commit=False)
            report.student = student
            
            report.supervisor = student.supervisor 
            report.report_id = f"WR-{student.student_id}-{report.week_num}"
            report.status = 'PENDING'
            report.save()
            messages.success(request, f"Weekly report for Week {report.week_num} submitted successfully.")
            return redirect('StudentTasks:my_weekly_reports')
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
    report = get_object_or_404(WeeklyReport, pk=report_id, supervisor=supervisor, status='PENDING' )
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
    report = get_object_or_404(WeeklyReport, pk=report_id, supervisor=supervisor, status='PENDING' )
    supervisor = get_object_or_404(Supervisor, user=request.user)

    if request.method == 'POST':
        comment = request.POST.get('supervisor_comment')

    if report.student.supervisor != supervisor:
        messages.error(request, "You are not authorized to reject this report.")
        return redirect('reject_weeklyreport', report_id=report_id )

    report.status = 'REJECTED'
    report.supervisor_comment = comment
    report.save()


    messages.warning(request, "Report rejected.")
    return redirect('supervisor_dashboard')


 
