from django.db import models
from django.utils import timezone
from Accounts.models import User
from decimal import Decimal

# Create your models here

# Loan interest rate per ₦1,000 borrowed
LOAN_INTEREST_PER_1000 = Decimal('10')

# Repayment options and loan status choices
REPAYMENT_CHOICES = [
    ('2m', '2 months'),
    ('4m', '4 months'),
    ('6m', '6 months')
]

LOAN_STATUS = [
    ('Pending', 'Pending'),
    ('Accepted', 'Accepted'),
    ('Rejected', 'Rejected'),
]


class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    repayment_plan = models.CharField(max_length=2, choices=REPAYMENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    loan_status = models.CharField(
    max_length=10,
    choices=LOAN_STATUS,
    default='Pending'
)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_repaid = models.BooleanField(default=False)

    @property
    def total_repayable(self):
        # Returns total amount to be repaid = principal + interest.
        return self.amount + self.interest

    @property
    def balance(self):
        # Returns the outstanding balance.
        return max(self.total_repayable - self.amount_paid, Decimal('0'))

    @property
    def status(self):
        # Returns a human-readable loan status.
        if self.loan_status == 'rejected':
            return "Rejected"
        if self.is_repaid:
            return "Repaid"
        if self.loan_status == 'approved':
            return "Active"
        return "Pending"

    def __str__(self):
        return f"{self.user.username} | ₦{self.amount} | {self.status}"


class LoanNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"To: {self.user.username} | {self.message[:40]}"
