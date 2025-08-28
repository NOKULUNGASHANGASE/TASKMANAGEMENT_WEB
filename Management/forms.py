from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Supervisor, Student
from django.core.exceptions import ValidationError

class SupervisorCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.filter(supervisor=None),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ("email", "password1", "password2", "first_name", "last_name")

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(username=email).exists():
            raise ValidationError("Email already exists")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  
        if commit:
            user.save()
        return user