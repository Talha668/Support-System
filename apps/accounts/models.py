from django.contrib.auth.models import AbstractUser
from django.db import models






class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('agent', 'Agent'),
        ('viewer', 'Viewer'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    max_capacity = models.IntegerField(default=10)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"