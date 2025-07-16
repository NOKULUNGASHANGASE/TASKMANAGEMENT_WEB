# forms.py
from django import forms
from .models import Contract, weeklytask
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
import math


  
class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['student', 'title', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }



class weeklytaskForm(forms.ModelForm):
    class Meta:
        model = weeklytask
        fields = ['date', 'title', 'task_list', 'absent_days', 'hours_spent' ]#'supervisor_comment']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            
        }

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop('contract', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        
        if self.contract and date:
            # Calculate week number
            delta = date - self.contract.start_date
            week_num = (delta.days // 7) + 1
            
            # Validate week number
            valid_weeks = [choice[0] for choice in self.contract.get_week_choices()]
            if week_num not in valid_weeks:
                self.add_error('date', "Cannot add tasks for this week (either future or invalid week).")
            
            # Add week_num to cleaned_data
            cleaned_data['week_num'] = week_num
            
            # Additional validations
            if date < self.contract.start_date:
                self.add_error('date', "Date cannot be before contract start date.")
            if date > timezone.now().date():
                self.add_error('date', "Cannot add tasks for future dates.")
        
        return cleaned_data
            
        


    