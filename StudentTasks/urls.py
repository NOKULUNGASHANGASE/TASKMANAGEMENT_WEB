
from django.urls import path, include
from . import views
from StudentTasks import views
from django.contrib.auth import views as auth_views
#from django.contrib import admin


app_name='StudentTasks'
urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', views.student_tasks_home, name='student_tasks_home'),
    path('contracts/', views.contract_list, name='contract_list'),
    path('contract_list/', views.contract_list, name='contract_list'),
    path('contract_create/', views.contract_create, name='contract_create'),
    path('contract/<int:contract_id>/weeklytasks/', views.weeklytask_list, name='weeklytask_list'),
    path('contract/<int:contract_id>/', views.contract_detail, name='contract_detail'),
    ##path('contract_detail/<int:contract_id>/', views.contract_detail, name='contract_detail'),
   ## path('contract_update/<int:contract_id>/', views.contract_update, name='contract_update'),
   ## path('contract_delete/<int:contract_id>/', views.contract_delete, name='contract_delete'),
    ##path('contract_detail/<int:contract_id>/', views.contract_detail, name='contract_detail'),
    

    # Task URLs
    path('contract/<int:contract_id>/weeklytasks/', views.weeklytask_list, name='weeklytask_list'),
    #path('contracts/<int:contract_id>/weeklytasks/', views.weeklytask_list, name='weeklytask_list'),
    path('weeklytask_create/<int:contract_id>/', views.weeklytask_create, name='weeklytask_create'),
    #path('weeklytask_detail/<int:pk>/', views.weeklytask_detail, name='weeklytask_detail'),
    #path('weeklytask_update/<int:pk>/', views.weeklytask_update, name='weeklytask_update'),
    #path('weeklytask_delete/<int:pk>/', views.weeklytask_delete, name='weeklytask_delete'),
    
    
    
]