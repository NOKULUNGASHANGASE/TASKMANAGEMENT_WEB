from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf.urls.static import static
import os
from .models import Task
from django.shortcuts import get_object_or_404
from datetime import timedelta
from Tasks.models import Task

def get_calendar_service(user_email=None):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    
    jsonPath = os.path.join(BASE_DIR, 'static','Tasks','json','task-calendar-sync-459909-4fa88ce7804f.json')
    credentials = service_account.Credentials.from_service_account_file(
       jsonPath,
       scopes=['https://www.googleapis.com/auth/calendar'],
       subject=user_email
    )
    service = build('calendar', 'v3', credentials=credentials)
    return service


def create_task(task_id):
    task = get_object_or_404(Task, pk=task_id)
    user_email = task.user.email  
    service = get_calendar_service(user_email)  

    print("service: ",service)
    # Calculate reminder minutes before due_date NBBB
    reminder_delta = task.due_date - task.reminder_time
    reminder_minutes = int(reminder_delta.total_seconds() // 60)
    if reminder_minutes < 0:
        reminder_minutes = 10   
    
    event = {
        'summary': task.title,
        'description': task.description,
        'start': {
            'dateTime': task.created,
            'timeZone': 'Africa/Johannesburg',
        },
        'end': {
            'dateTime': task.datecomplited,
            'timeZone': 'Africa/Johannesburg',
        },
        'reminders': {
        'useDefault': False,
        'overrides': [
        {'method': 'email', 'minutes': 24 * 60},
        {'method': 'popup', 'minutes': 10},
        ],
        },
    }
    
    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"Error creating Task: {e}")
      

