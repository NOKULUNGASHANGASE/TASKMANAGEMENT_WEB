from django.contrib import admin
from . models import *



class tasksadmin(admin.ModelAdmin):
    readonly_fields = ('created',)
    
    
admin.site.register(Task, tasksadmin )
admin.site.register( YearPlan)
admin.site.register(StudentTask)
admin.site.register(ActivityLog)
admin.site.register(Message)
admin.site.register(Notification)

