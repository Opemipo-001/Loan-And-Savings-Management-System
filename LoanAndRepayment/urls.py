from django.urls import path
from . import views

urlpatterns = [
    path('apply/', views.apply_for_loan, name='apply-loan'),
    path('check-status/', views.check_loan_status, name='check-loan-status'),
    path('repay/<int:loan_id>/', views.repay_loan, name='repay-loan'),
    path('history/', views.loan_history, name='loan-history'),
    path('dashboard/', views.user_dashboard_summary, name='user-dashboard'),
    path('repayment-schedule/<int:loan_id>/', views.repayment_schedule, name='repayment-schedule'), # Repayment breakdown
    path('notifications/', views.loan_notifications, name='loan-notifications'),
    #Admin path
    path('admin/all-loans/', views.admin_view_all_loans, name='admin-all-loans'),
    path('update-status/<int:loan_id>/', views.update_loan_status, name='update-loan-status'),
]

