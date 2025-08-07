from django.db import models
from django.contrib.auth.models import AbstractUser 
from datetime import timedelta, datetime
from django.utils import timezone

# Create your models here.
USER_TYPES = [
    ('member', 'Member'),
    ('admin', 'Admin')
]

LOCK_DURATIONS = [
    ('2d', '2 Days'),
    ('1w', '1 Week'),
    ('1m', '1 Month'),
    ('3m', '3 Months'),
    ('6m', '6 Months'),
    ('1y', '1 Year'),
]

DURATION_MAP = {
    '2d': timedelta(days=2),
    '1w': timedelta(weeks=1),
    '1m': timedelta(days=30),
    '3m': timedelta(days=90),
    '6m': timedelta(days=180),
    '1y': timedelta(days=365),
}

class User(AbstractUser):
    username = models.CharField(max_length=20, blank=False, unique=True)
    email= models.EmailField(max_length=50, unique=True, blank=False)
    phone_number = models.CharField(max_length=15, unique=True, blank=False)
    address= models.CharField(max_length=50)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='member')
    balance= models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    is_locked=models.BooleanField(default=True)
    lock_duration=models.CharField(max_length=5, choices=LOCK_DURATIONS, null=False, blank=False)
    lock_start = models.DateTimeField(default= timezone.now)
    
    
    def __str__ (self):
        return self.username
    
    from django.utils import timezone

def check_unlock_status(self):
    unlock_time = self.calculate_unlock_time()
    now = timezone.now()  

    if now >= unlock_time and not self.interest_credited:
        interest = self.calculate_interest()
        self.user.balance += interest
        self.user.save()
        self.interest_credited = True
        self.save()
