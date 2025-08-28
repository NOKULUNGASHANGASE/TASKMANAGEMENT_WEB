"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
""" 
from django.contrib import admin
from django.urls import path, include
from Tasks import views
from Tasks.views import signupuser
from django.contrib.auth import views as auth_views
from Tasks import emailing




urlpatterns = [
    path('admin/', admin.site.urls),
    #home page
    path('', views.home, name='home'),
     path('supervisor_dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    #student tasks app url path
    #path('studenttasks/', include('StudentTasks.urls')),
    #path('student/', include('StudentTasks.urls', namespace='StudentTasks')),
    path('students/', include(('StudentTasks.urls', 'StudentTasks'), namespace='StudentTasks')),

    
    #Auth
    path('signup/', views.signupuser, name='signupuser'), #signup/
    path('signup/', signupuser, name='signupuser'),
    
    path('logoutuser/', views.logoutuser, name='logoutuser'),
    path('loginuser/', views.loginuser, name='loginuser'),
     #tasks pages
    path('Mytasks/', views.Mytasks, name='Mytasks'),
    path('createtask/', views.createtask, name='createtask'),
    path('supervisor_assign_task/', views.supervisor_assign_task, name='supervisor_assign_task'),
    #help user to be able to create the form without signing in
    path('accounts/login',views.loginuser, name="loginuser" ),
    path('update_user/<int:task_pk>/', views.update_user, name='update_user'),
    path('task/<int:task_pk>',views.viewtasks, name='viewtasks' ),
    path('task/<int:task_pk>/complete',views.completetasks, name='completetasks' ),
    path('completed',views.completedtasks, name='completedtasks' ),
    path('task/<int:task_pk>/delete',views.deletetasks, name='deletetasks' ),
   # year plan calender create and view
    #path('create_year_plan/', views.create_year_plan, name='create_year_plan'),
    path('view_year_plan/', views.view_year_plan, name='view_year_plan'),
    path('create_year_plan/<int:student_id>/', views.create_year_plan, name='create_year_plan'),
    
    # urls.py
    path('supervisor_assign_task/', views.supervisor_assign_task, name='supervisor_assign_task'),
    path('create_year_plan/', views.create_year_plan, name='create_year_plan'),

    # And this one too:
    #path('assign_task/<int:student_id>/', views.supervisor_assign_task, name='supervisor_assign_task'),
    #path('supervisor_assign_task/<int:student_id>/', views.supervisor_assign_task, name='supervisor_assign_task'),

    #email cornfirmation
    
    
    #password reset
    path('password_reset/',auth_views.PasswordResetView.as_view(template_name='Tasks/password_reset.html'), name='password_reset'),
    path('password_reset_done/',auth_views.PasswordResetDoneView.as_view(template_name='Tasks/reset_done.html'), name='password_reset_done'),
    path('password_reset_confirm/ <uidb64>/<token>',auth_views.PasswordResetConfirmView.as_view(template_name='Tasks/reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset_complete',auth_views.PasswordResetCompleteView.as_view(template_name='Tasks/reset_complete.html'), name='password_reset_complete'),
    path('update_user/password/',auth_views.PasswordChangeView.as_view(template_name='Tasks/PasswordChange.html'),name='password_change'),
    path('update_user/password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='Tasks/PasswordChangeDone.html'), name='password_change_done'),
    path('initial_password_change/', views.initial_password_change, name='initial_password_change'),
   
    path('activate/<uidb64>/<token>', emailing.activate, name="activate"),
    
    #API App url path 
    path('api/', include('api.urls')),
    path('Management', include('Management.urls')),
     

    
    
]   
