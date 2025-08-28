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
from django.conf import settings


def send_task_email(task, subject, message):
    from .models import StudentTasks
    student_email = task.contract.student.user.email
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,  # django default will customize later
        [student_email],
        fail_silently=False
    )