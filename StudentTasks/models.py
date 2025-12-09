from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
from datetime import timedelta
import calendar
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError


class Contract(models.Model): 
    contract_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    title = models.CharField(max_length=100, default="UWS intern Contract")
    description = models.TextField(blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)
    total_hours = models.PositiveIntegerField(editable=False, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    terms_and_conditions = models.TextField(blank=True, null=True)
    progress = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)


    def generate_time_periods(self):
        return "Generated time periods"
    @property
    def contract_progress(self):
        """Calculate overall progress percentage for dashboard"""
        # Time-based progress
        total_days = (self.end_date - self.start_date).days
        days_passed = (timezone.now().date() - self.start_date).days
        time_progress = min(100, max(0, (days_passed / total_days) * 100)) if total_days > 0 else 0
        
        # Task-based progress
        total_expected_hours = sum(task.expected_hours for task in self.weeklytask_set.all())
        completed_hours = sum(task.hours_spent for task in self.weeklytask_set.filter(status='COMPLETED'))
        task_progress = (completed_hours / total_expected_hours * 100) if total_expected_hours > 0 else 0
        
        # Weighted average (50% time, 50% tasks)
        return round((time_progress * 0.5) + (task_progress * 0.5))
    
    @property
    def weeks_completed(self):
        """Number of weeks completed in contract"""
        return self.weeklyreport_set.filter(status='COMPLETED').count()
    
    @property
    def weeks_remaining(self):
        """Number of weeks remaining in contract"""
        total_weeks = ((self.end_date - self.start_date).days // 7) + 1
        return total_weeks - self.weeks_completed

    def total_days(self):
        days = 0
        current = self.start_date
        while current <= self.end_date:
            if current.weekday() < 5:  # Weekdays only (Mon–Fri)
                days += 1
            current += timezone.timedelta(days=1)
        return days

    def total_day_hours(self):
        return self.total_days() * 8
 
    
    def total_w_hours(self):
        return sum(task.hours_spent for task in self.weeklyreport_set.all())

    def progress_percent(self):
        total = self.total_day_hours()
        if total == 0:
            return 0
        return round((self.total_w_hours() / total) * 100, 2)
    
    def get_week_choices(self):
        """Generate week number choices based on contract dates and current date"""
        today = timezone.now().date()
        choices = []
        current_week_start = self.start_date
        week_num = 1
        
        while current_week_start <= self.end_date:
            week_end = current_week_start + timezone.timedelta(days=6)
            
            # Only include weeks that have ended or are current
            if week_end <= today or (current_week_start <= today <= week_end):
                week_str = f"Week {week_num} ({current_week_start.strftime('%d %b')} - {week_end.strftime('%d %b')})"
                choices.append((week_num, week_str))
            
            current_week_start += timezone.timedelta(days=7)
            week_num += 1
        
        return choices
    def get_week_dates(self, week_num):
        """Get start and end dates for a specific week number"""
        week_start = self.start_date + timezone.timedelta(days=(week_num-1)*7)
        week_end = week_start + timezone.timedelta(days=6)
        return week_start, week_end

    


class WeeklyReport(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    report_id=models.CharField(max_length=20, unique=True)
    student = models.ForeignKey('Management.Student', on_delete=models.CASCADE, related_name='weekly_reports')
    supervisor = models.ForeignKey('Management.Supervisor', on_delete=models.CASCADE, related_name='weekly_reports',  null=True, blank=True)
    week_num = models.IntegerField(null=True, blank=True)
    date = models.DateField()
    title = models.CharField(max_length=200)
    daily_duties = models.TextField(help_text="Describe daily tasks performed during the week.")
    absent_days = models.PositiveIntegerField(default=0, help_text="Number of absent days this week")
    hours_spent = models.FloatField()
    supervisor_comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    class Meta:
        ordering = ['-week_num']
        unique_together = ['student', 'week_num']  # Each week can only have one report per contract

    def clean(self):
        # Hours validation
        if self.hours_spent > 8 * (5 - min(self.absent_days, 5)):
            raise ValidationError("Hours spent cannot exceed allowed working hours for the week.")
        
        # Date validation: weekdays only
        if self.date.weekday() >= 5:
            raise ValidationError("Tasks can only be created on weekdays (Mon–Fri).")
        
        # Ensure contract exists
        if not self.contract:
            raise ValidationError("A valid contract is required.")

        # Validate absent_days
        if self.absent_days > 5:
            raise ValidationError("Cannot have more than 5 absent days in a week.")

        # Validate week_num against contract
        valid_weeks = [choice[0] for choice in self.contract.get_week_choices()]
        if self.week_num not in valid_weeks:
            raise ValidationError(f"Invalid week number. Allowed weeks: {valid_weeks}")

        # Validate date within week range
        week_start, week_end = self.contract.get_week_dates(self.week_num)
        if not (week_start <= self.date <= week_end):
            raise ValidationError(f"Date must fall within Week {self.week_num} ({week_start} to {week_end})")
        
        # Ensure report date is not in the future
        if self.date > timezone.now().date():
            raise ValidationError("Cannot add tasks for future dates.")

    def expected_hours(self):
        """Calculate expected hours considering absent days."""
        weekdays = 5 - min(self.absent_days, 5)  # max 5 working days
        return weekdays * 8

    def progress_percentage(self):
        if self.expected_hours() == 0:
            return 0
        return round((self.hours_spent / self.expected_hours()) * 100, 2)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - Week {self.week_num}: {self.title}"
 
    
