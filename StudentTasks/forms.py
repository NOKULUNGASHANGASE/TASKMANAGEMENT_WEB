# forms.py
from django import forms
from .models import Contract, WeeklyReport
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
import math



  
class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['contract_id','title', 'description', 'start_date', 'end_date', 'terms_and_conditions', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise ValidationError("End date cannot be before start date.")

        if start_date and start_date < timezone.now().date():
            raise ValidationError("Start date cannot be in the past.")

        return cleaned_data


class WeeklyReportForm(forms.ModelForm):
    class Meta:
        model = WeeklyReport
        fields = ['week_num', 'date', 'title', 'daily_duties', 'absent_days', 'hours_spent']

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        self.contract = kwargs.pop('contract', None)
        super().__init__(*args, **kwargs)

        # If student is provided but no contract, get their active contract
        if self.student and not self.contract:
            active_contract = Contract.objects.filter(student=self.student).order_by('-start_date').first()
            if active_contract:
                self.contract = active_contract
                self.instance.contract = active_contract

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')

        if self.contract and date:
            # Calculate week number based on contract start date
            delta = date - self.contract.start_date
            week_num = (delta.days // 7) + 1

            # Validate week number
            valid_weeks = [choice[0] for choice in self.contract.get_week_choices()]
            if week_num not in valid_weeks:
                self.add_error('date', "Cannot add tasks for this week (either future or invalid week).")

            # Assign calculated week_num
            cleaned_data['week_num'] = week_num

            # Additional validations
            if date < self.contract.start_date:
                self.add_error('date', "Date cannot be before contract start date.")
            if date > timezone.now().date():
                self.add_error('date', "Cannot add tasks for future dates.")

            # Validate hours and absent_days
            absent_days = cleaned_data.get('absent_days', 0)
            hours_spent = cleaned_data.get('hours_spent', 0)
            if absent_days < 0 or absent_days > 5:
                self.add_error('absent_days', "Absent days must be between 0 and 5.")
            if hours_spent < 0 or hours_spent > 8 * (5 - min(absent_days, 5)):
                self.add_error('hours_spent', "Hours spent cannot exceed allowed working hours for the week.")

        return cleaned_data




        


    