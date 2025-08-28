from django.db import models
from django.contrib.auth.models import User


class Admin(models.Model):
    AdminID=models.AutoField(primary_key=True)
    user=models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    Designation=models.CharField(max_length=30, null=False, blank=False)

    def __str__(self):
        return f"Admin: {self.user.get_full_name()}"
 


class Supervisor(models.Model):
    STATUS_CHOICES = [('active', 'Active'),('inactive', 'Inactive'),]
    supervisorID=models.AutoField(primary_key=True)
    user=models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    Admin=models.ForeignKey(Admin, null=True, blank=True, on_delete=models.CASCADE)
    initial_password = models.CharField(max_length=128, blank=True, null=True)
    status=models.CharField(max_length=20, default='active')

    def __str__(self):
        return f"Supervisor: {self.user.get_full_name()}"
    
    def active_students_count(self):
        return self.student_set.filter(active=True).count()


class Student(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.SET_NULL, null=True, blank=True)
    student_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Student: {self.user.get_full_name()}"
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']