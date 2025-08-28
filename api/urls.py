from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet
from . import views



router = DefaultRouter()
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
     #tasks pages
    path('', views.apiOverview, name="api-overview"),
    path('task-list/', views.taskList, name='task-list'),
    path('task-detail/<str:pk>/', views.taskDetail, name='task-detailS'),
    path('task-create/', views.taskCreate, name='task-create'),
    path('task-update/<str:pk>/', views.taskUpdate, name='task-update'),
    path('task-delete/<str:pk>/',views.taskDelete, name='task-delete' ),
    path('user-task-summary/<str:email>', views.user_task_summary, name='user-task-summary'),
    path('assigned/', views.assigned_tasks, name='assigned_tasks'),
    path('complete/<int:task_id>/', views.complete_task, name='complete_task'),
    path('year-plan-events/', views.year_plan_events_json, name='year_plan_events_json'),
    path('year_plan_events_api/', views.year_plan_events_api, name='year_plan_events_api'),

]