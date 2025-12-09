
from django.urls import path, include
from . import views
from StudentTasks import views
from django.contrib.auth import views as auth_views
#from django.contrib import admin


app_name='StudentTasks'
urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', views.student_tasks_home, name='student_tasks_home'),
    path('contract_create/', views.contract_create, name='contract_create'),
    path('contract/<int:pk>/', views.contract_detail, name='contract_detail'),
    path('contract/<int:pk>/update/', views.contract_update, name='contract_update'),
    path('contract/<int:pk>/delete/', views.contract_delete, name='contract_delete'),
    path('contract_list/', views.contract_list, name='contract_list'),
    # Reports URLs
    path('create_weekly_report/', views.create_weekly_report, name='create_weekly_report'),
    path('my_weekly_reports/', views.my_weekly_reports, name='my_weekly_reports'),

    # Supervisor views
    path('review_weekly_reports/', views.review_weekly_reports, name='review_weekly_reports'),
    path('approve_weeklyreport/<int:report_id>/', views.approve_weeklyreport, name='approve_weeklyreport'),
    path('reject_weeklyreport/<int:report_id>/', views.reject_weeklyreport, name='reject_weeklyreport'),
    
    

    
]