from django.db import models
from django.utils import timezone
from Accounts.models import User, DURATION_MAP
from datetime import timedelta
from decimal import Decimal

INTEREST_RATE = Decimal('0.05')  # 5%

class Savings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    lock_duration = models.CharField(max_length=5)
    unlock_time = models.DateTimeField()
    interest_credited = models.BooleanField(default=False)
    is_withdrawn = models.BooleanField(default=False)

    def calculate_unlock_time(self):
        return self.created_at + DURATION_MAP.get(self.lock_duration, timedelta(0))

    def calculate_interest(self):
        return self.amount * INTEREST_RATE

    def check_unlock_status(self):
        unlock_time = self.unlock_time
        now = timezone.now()

        if now >= unlock_time and not self.interest_credited:
            interest = self.calculate_interest()

            # Credit interest to user balance
            self.user.balance += interest
            self.user.save()

            self.interest_credited = True
            self.save()

            Notification.objects.create(
                user=self.user,
                message=f"Interest of ₦{interest:.2f} has been credited for your saving of ₦{self.amount}."
            )

    @property
    def can_withdraw(self):
        return timezone.now() >= self.unlock_time and not self.is_withdrawn

    def __str__(self):
        return f"{self.user.username} - ₦{self.amount} saved on {self.created_at.strftime('%Y-%m-%d')}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"To: {self.user.username} | {self.message[:50]}"

