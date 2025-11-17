from mailbox import Message
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django import forms
from .models import Task, StudentTask,YearPlan, Notification, Message
from django_flatpickr.widgets import DatePickerInput
from Management.models import Admin
from Management.models import Student, Supervisor




class StudentTaskForm(ModelForm):
    
    class Meta:
       
       model= StudentTask
       fields = ['student', 'task', 'completed', 'remarks']
       widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'task': forms.Select(attrs={'class': 'form-select'}),
            'completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
       
       
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Task details'}),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'ms-TextField-field form-control',
                'type': 'date', 
                'aria-describedby': 'datePickerHelp',
                'data-is-focusable': 'true',
             }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'ms-TextField-field form-control',
                'type': 'date', 
                'aria-describedby': 'datePickerHelp',
                'data-is-focusable': 'true',
             }),
            
            
        }
    

    
class SignUpForm(UserCreationForm):
    class Meta:
       model= User
       fields=['email', 'first_name','last_name', 'password1', 'password2' ]
       widgets = {
            
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            
  
        }
       help_texts = {
            'password1': None,
            'password2': None,
        }
       
       
class UpdateUserForm(UserChangeForm):
    class Meta:
       model= User
       fields=['first_name','last_name', 'email' ]
       widgets = {
            
            'email': forms.DateInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            
  
        }
       help_texts = {
            'password1': None,
            'password2': None,
        }

class UserUpdateForm(UserChangeForm):
   
    class Meta:
        model= User
        fields=['first_name','last_name', 'email', 'password' ]
        widgets = {
                
                'email': forms.DateInput(attrs={'class': 'form-control'}),
                'first_name': forms.TextInput(attrs={'class': 'form-control'}),
                'last_name': forms.TextInput(attrs={'class': 'form-control'}),
                'contact_details': forms.PasswordInput(attrs={'class': 'form-control'}),
                'about': forms.PasswordInput(attrs={'class': 'form-control'}),
    
            }
    
       
class YearPlanForm(forms.ModelForm):
    class Meta:
        model = YearPlan
        fields = ['title', 'description', 'student', 'start_date', 'end_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }



class BulkTaskForm(forms.Form):
    students = forms.ModelMultipleChoiceField(queryset=Student.objects.all())
    title = forms.CharField(max_length=200)
    description = forms.Textarea()
    due_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter message subject'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Type your message here...'}),
            'recipient': forms.Select(attrs={'class': 'form-select'}),
        }

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Type your reply here...'}),
        }