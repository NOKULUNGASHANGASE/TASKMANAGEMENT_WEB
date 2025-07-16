from django.forms import ValidationError
from django.shortcuts import render,redirect, reverse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm 
from django.contrib.auth.decorators import login_required
from .forms import TaskForm, SignUpForm, UserUpdateForm 
from .models import Task
from .models import Task
from django.contrib import messages
from django.template.defaultfilters import date
from django.utils import timezone
from .emailing import *
from Tasks.google_calendar import create_task
from Tasks import emailing

def home(request):
 # messages.warning(request, "this is a test message")
  return render(request, 'Tasks/home.html')
  
def tasks_home(request):
 # messages.warning(request, "this is a test message")
  return render(request, 'Tasks/tasks_home.html')

def signupuser(request):
  
  form=SignUpForm()  #Creates an empty instance of the SignUpForm. This form will be used to render fields on the signup page.
  
  payload = {
      "form":form       #Prepares a dictionary (payload) containing the form instance. This dictionary will be passed to the template for rendering.
    } 
  if request.method =='GET':  
    return render(request, 'Tasks/signupuser.html', payload) #Checks if the request method is GET. If true:Renders the Tasks/signupuser.html template.
  
  if request.method == 'POST':           # Checks if the request method is POST. If true:Creates a new instance of SignUpForm populated with data from request.POST
    form= SignUpForm(request.POST)
    if form.is_valid():              # Validates the form data. If all fields meet validation criteria, proceeds to process the data
      email=form.cleaned_data['email'].lower()
      password1= form.cleaned_data['password1']
      password2= form.cleaned_data['password2']
    
      if password1 != password2:
        return render(request, 'Tasks/signupuser.html', {'form': form,'error': 'Passwords did not match'})
      
      try:
       if form.is_valid():  
        user = form.save(commit=False)  # Don't save immediately  
        user.username = form.cleaned_data['email']  # Set email as username  
        user.first_name = form.cleaned_data['first_name']  
        user.last_name = form.cleaned_data['last_name']  
        user.email = form.cleaned_data['email']  
        user.is_active = False  # Disable account until email verification  
        user.save()  # Now save with all fields  
        
      except IntegrityError:
        return render(request, 'Tasks/signupuser.html', {'form':SignUpForm(), 'error': 'Email already exists'})
        
        
      #new_user=authenticate(username=email, password=password1)  # Authenticates the newly created user using their email (as username) and password. Returns a user object if authentication is successful; otherwise, returns None.
      if sendActivationEmail(request, user):   
          messages.success(request, f"Activation email sent to {user.email} access you inbox to activate your account.")
      else:
          messages.error(request, "Somthing went wrong while sending activation email please contact support.")
          user.delete()  # Clean up if email fails
          return render(request, 'Tasks/signupuser.html', {'form': form,'error': 'Account creation failed - please try again'})
              
            #we send email
      return redirect('home')
    
    form= SignUpForm() 
  return render(request, 'Tasks/signupuser.html', {'form':SignUpForm(), 'error': 'please fix the errors and try again'})  ###this is causing the error
         

@login_required
def update_user(request, task_pk):
    user_instance = get_object_or_404(User, pk=task_pk)  # Fetch the user instance
    #form=UserUpdateForm()
    #if request.method =='GET':  
         #return redirect('update_user', task_pk=1)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user_instance)
        
        if form.is_valid():
            form.save()
            login(request, user_instance)
            messages.success(request,"your profile has been updated")
            return redirect('Mytasks')  # Redirect after successful update
    else:
      print("user_instance: ", user_instance.first_name)
      form = UserUpdateForm(instance=user_instance)  # Show form with user data
    
      # Add rendering for the form template
      return render(request, 'Tasks/updateuser.html', {'form': form})
    
@login_required
def PasswordChange(request):
    if request.method == "POST":
        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "Password changed successfully.")
            return redirect("update_user")
    return render(request, "Tasks/passwordChange.html")
  
  

        
def loginuser(request):
  if request.method=='GET':
      
    return render(request, 'Tasks/Loginuser.html',{'form': AuthenticationForm()})
  else:
    user=authenticate(request,username=request.POST['username'], password=request.POST['password'])
    if user is None:
      return render(request, 'Tasks/Loginuser.html', {'form':AuthenticationForm(), 'error':'user and password did not match'})
    else:
      login(request, user)
      return redirect('Mytasks')
      
def logoutuser(request):
    if request.method == 'POST':
      logout(request)
      return redirect('home') 

  
@login_required  
def Mytasks (request):
     tasks=Task.objects.filter(user=request.user, datecomplited__isnull=True)
     search_input = request.GET.get('search-area') or ''
    
     if search_input:
        tasks = tasks.filter(title__icontains=search_input)  

     context = {'tasks': tasks}
     return render(request, 'Tasks/MyTasks.html', context)

@login_required
def createtask(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            try:
                task.full_clean()  # Explicit validation
                task.save()
                return redirect('task-list')
            except ValidationError as e:
                form.add_error(None, e)  # Add validation errors to form
        return render(request, 'tasks/createtask.html', {'form': form})
    else:
        form = TaskForm()
    return render(request, 'tasks/createtask.html', {'form': form})

@login_required
def viewtasks(request, task_pk):
  #users to view their list denie access to athor users 
  task= get_object_or_404(Task, pk=task_pk, user=request.user)
  if request.method == 'GET':
    form=  TaskForm( instance=task)
    return render(request, 'Tasks/viewtasks.html', {'task':task, 'form':form})
  else:
    try:
      form = TaskForm(request.POST, instance=task)
      form.save()
      return redirect('Mytasks') 
    except ValueError:
      return render(request,'Tasks/viewtasks.html', {'task':task, 'error':'band information'}, )
    
#allow the user to complet their tasks and it remive it from the task list  
@login_required
def completetasks(request, task_pk):
  task= get_object_or_404(Task, pk=task_pk, user=request.user)
  if request.method == 'POST':

    task.datecomplited = timezone.now()
    task.status = "Completed"
    task.save()
    return redirect('Mytasks')
  
 #allow the user to view their completed task show the completed date. 
@login_required
def completedtasks(request ):
  
  tasks=Task.objects.filter(user=request.user, datecomplited__isnull=False).order_by('-datecomplited')
     
  return render(request, 'Tasks/completedtasks.html', {'tasks':tasks})
  
@login_required  
def deletetasks(request, task_pk):
  task= get_object_or_404(Task, pk=task_pk, user=request.user)
  if request.method == 'POST':
    task.datecomplited = timezone.now()
    task.delete()
    return redirect('Mytasks')
  
@login_required
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES).keys():
            task.status = new_status
            if new_status == 'completed':
                task.completed_at = timezone.now()
            task.save()
            messages.success(request, 'Task status updated!')
    return redirect('Mytasks')
  




  
  


          
        