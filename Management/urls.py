from django.urls import path
from . import views

urlpatterns = [
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create_supervisor/', views.create_supervisor, name='create_supervisor'),
    path('assign_students/<int:supervisor_id>/', views.assign_students, name='assign_students'),
    
]