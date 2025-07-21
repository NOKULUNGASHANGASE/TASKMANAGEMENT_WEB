from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django import forms
from .models import Task, models
from django_flatpickr.widgets import DatePickerInput
from Management.models import Admin
from Management.models import Student




class TaskForm(ModelForm):
    assigned_to_student = forms.ModelChoiceField(queryset=Student.objects.none())
    class Meta:
       
       model= Task
       fields=['title', 'description', 'due_date','important', ]
       widgets = {
            
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
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
            'important': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
       def __init__(self, *args, **kwargs):
        supervisor = kwargs.pop('supervisor', None)
        super().__init__(*args, **kwargs)
        if supervisor:
            self.fields['assigned_to_student'].queryset = Student.objects.filter(supervisor=supervisor)

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
       
class SupervisorSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    admin = forms.ModelChoiceField(queryset=Admin.objects.all(), required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2', 'admin']

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email
       
