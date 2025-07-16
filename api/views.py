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



    