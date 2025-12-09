from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError




class Task(models.Model):
    task_id = models.IntegerField(null=True, blank=True)
    
    supervisor = models.ForeignKey("Management.Supervisor", on_delete=models.CASCADE, related_name='tasks')
    title= models.CharField(max_length=100)
    description= models.CharField(max_length=250)
    file = models.FileField(upload_to='Newtasks/' , blank=True, null=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    created= models.DateTimeField( auto_now_add=True)
    due_date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title
    
class StudentTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    
    studenttask_id=models.CharField(max_length=20, unique=True)
    student = models.ForeignKey( "Management.Student", on_delete=models.CASCADE, related_name='student_tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assigned_students')
    assigned_date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    date_completed=models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50,default="Pending")
    reminder_time = models.DateTimeField(default=timezone.now)
    reminder_sent = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.task.title}" 
    
    def is_overdue(self):
        return self.due_date < timezone.now() and self.status != 'completed'
    
    def save(self, *args, **kwargs):
        if self.is_overdue():
            self.status = 'overdue'
        super().save(*args, **kwargs) 

    @property
    def status(self):
        
        if self.completed:
            return "Completed"
        elif self.is_overdue:
            return "Overdue"
        return "Pending"

class YearPlan(models.Model):
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='yearplans_as_student')
    supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='yearplans_as_supervisor')
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.title} ({self.student.username})"
    
class ActivityLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    description = models.TextField()
    
    class Meta:
        ordering = ['-timestamp']

   

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message

class Message(models.Model):
    sender = models.ForeignKey("Management.Student", on_delete=models.CASCADE, default=1)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    


    def __str__(self):
        return self.subject







   
        

 
    




    
    
    
