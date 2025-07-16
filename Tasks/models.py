from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from Management.models import Student, Supervisor



class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    title= models.CharField(max_length=100)
    description= models.CharField(max_length=250)
    file = models.FileField(upload_to='Newtasks/' , blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    user=models.ForeignKey(User, on_delete=models.CASCADE)  # on_delete=models.CASCADE
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE, null=True, blank=True)
    created= models.DateTimeField( auto_now_add=True)
    datecomplited=models.DateTimeField(null=True, blank=True)
    important = models.BooleanField(default=False)    
    due_date = models.DateTimeField(default=timezone.now)
    reminder_time = models.DateTimeField(default=timezone.now)
    reminder_sent = models.BooleanField(default=False)
    status = models.CharField(max_length=50,default="Pending")
    #def clean(self):
        #if self.reminder_time>= self.due_date:
           # raise ValidationError("Reminder time must be before the due date.")
    
    def is_overdue(self):
        return self.due_date < timezone.now() and self.status != 'completed'
    
    def save(self, *args, **kwargs):
        if self.is_overdue():
            self.status = 'overdue'
        super().save(*args, **kwargs)

   
        

 
    




    
    
    
