from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import messages
from celery import shared_task
from django.utils import timezone
from .models import Task




def sendActivationEmail(request, user):
    
    mail_subject= "Activate your account: "+user.first_name+" "+user.last_name
    
    message = render_to_string('Tasks/activationEmail.html',{
       "user":user,
       "domain":get_current_site(request).domain,
       "uid":urlsafe_base64_encode(force_bytes(user.pk)),
       "token":default_token_generator.make_token(user),
       "protocol": 'https' if request.is_secure() else 'http'
    })
    
    return send_mail(mail_subject,f'{message}', '',[f'{user.email}'],fail_silently=False)
    
    
    
def activate(request, uidb64, token):
  
    try:
      uid = force_str(urlsafe_base64_decode(uidb64))
      user = User.objects.get(pk = uid)
    except:
        user = None
        
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Account activated successfully, welcome.")
    else:
        messages.success(request, "Something went wrong while activating account please contact support.")
        pass    
    
    return redirect('home')
        


@shared_task
def send_task_reminders():
    now = timezone.now()
    tasks = Task.objects.filter(reminder_time__lte=now, reminder_sent=False)
    for task in tasks:
        send_mail(
            'Task Reminder',
            f'Reminder: {task.title}\n{task.description}',
            'from@example.com',
            [task.user.email],
        )
        task.reminder_sent = True
        task.save()
        

#def send_deadline_reminder():
    #upcoming_tasks = Task.objects.filter(due_date__lt=timezone.now() + timedelta(days=2))
    #for task in upcoming_tasks:
        #send_mail(
            #f'Reminder: Task "{task.title}" is due soon!',
            #f'Your task "{task.title}" is due on {task.due_date}. Make sure to complete it on time.',
            #'from@example.com',
          #  [task.user.email]
       # )

