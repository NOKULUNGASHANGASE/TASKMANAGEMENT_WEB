from datetime import timedelta, timezone
from django.shortcuts import render
from rest_framework import viewsets
from Tasks.models import Task
from .serializers import TaskSerializer
from django.http import JsonResponse
from rest_framework.decorators import api_view
from Tasks.google_calendar import create_task
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
from Management.models import Student
from Tasks.models import YearPlan
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    

@api_view(['GET'])
def apiOverview(request):
    api_urls ={
        
        'List': '/tasks/',
        'Detail View': '/tasks/<int:pk>/',
        'Create': '/tasks/create/',
        'Update': '/tasks/update/<int:pk>/',
        'Delete': '/tasks/delete/<int:pk>/',
    }
    return JsonResponse(api_urls)

@api_view(['GET'])
def taskList(request):
    tasks=Task.objects.all()
    serializer=TaskSerializer(tasks,many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['GET'])
def taskDetail(request, pk):
    tasks=Task.objects.get(id=pk)
    serializer=TaskSerializer(tasks,many=True)
    return JsonResponse(serializer.data)

@api_view(['POST'])
def taskCreate(request):
    
    serializer=TaskSerializer(data=request.data)
    if serializer.is_valid():
        task=serializer.save()
        create_task(task.id)

        return JsonResponse(serializer.data, status=201) 
    return JsonResponse(serializer.error, status=400)      
    

@api_view(['POST'])
def taskUpdate(request,pk):
    tasks=Task.objects.get(id=pk)
    serializer=TaskSerializer(instance=tasks, data=request.data)
    if serializer.is_valid():
        serializer.save()
    return JsonResponse(serializer.data)

@api_view(['DELETE'])
def taskDelete(request,pk):
    task=Task.objects.get(id=pk)
    task.delete()
    return JsonResponse('Task successfully deleted')

@api_view(['GET'])
def user_task_summary(request, email):
    user = User.objects.get(email = email)
    tasks = Task.objects.filter(user=user)
    userTasks = []
    for  task in tasks:
        userTasks.append({
            "title": task.title
        })
    data = {
        "user": 
            {
                "Name": user.first_name,
                "Surname": user.last_name,
                "Email Address": user.email,
                "Tasks": {
                    "Total number of tasks": tasks.count(),
                    "Total number of completed tasks": tasks.filter(status = "Completed").count(),
                    "userTasks":userTasks
                }
            }
        ,
        
        
    }
    
    return JsonResponse(data)

def assigned_tasks(request):
    tasks = Task.objects.filter(assigned_to=request.user, status='PENDING')
    data = {
        "tasks": [{
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date.strftime("%Y-%m-%d"),
            "status": task.status,
        } for task in tasks]
    }
    return JsonResponse(data)

@csrf_exempt
@require_POST
@login_required
def complete_task(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
        task.status = "COMPLETED"
        task.datecomplited = timezone.now()
        task.save()
        return JsonResponse({"success": True, "message": "Task completed."})
    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found."}, status=404)

@login_required
def year_plan_events_json(request):
    plans = YearPlan.objects.filter(student=request.user)
    events = []

    for plan in plans:
        events.append({
            "title": plan.title,
            "start": plan.start_date.isoformat(),
            "end": plan.end_date.isoformat(),
            "description": plan.description,
        })

    return JsonResponse(events, safe=False)



@login_required
@require_GET
def year_plan_events_api(request):
    student = get_object_or_404(Student, user=request.user)
    plans = YearPlan.objects.filter(student=student.user)  
    #plans = YearPlan.objects.filter(student=student)

    events = []
    for plan in plans:
        events.append({
            'id': plan.id,
            'title': plan.title,
            'start': plan.start_date.isoformat(),
            'end': (plan.end_date + timedelta(days=1)).isoformat(),  
            'description': plan.description,
        })

    return JsonResponse(events, safe=False)

    