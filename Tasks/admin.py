from django.contrib import admin
from . models import *



class tasksadmin(admin.ModelAdmin):
    readonly_fields = ('created',)
    
    
admin.site.register(Task, tasksadmin )
admin.site.register( YearPlan)


