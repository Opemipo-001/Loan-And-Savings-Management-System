from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from decimal import Decimal
from .models import Loan, LoanNotification
from .serializers import LoanSerializer
from datetime import timedelta

# Create Your views here

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_for_loan(request):
    serializer = LoanSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        loan = serializer.save()
        
        # Notify user
        LoanNotification.objects.create(
            user=request.user,
            message=f"Loan of ₦{loan.amount} is pending approval."
        )

        # Notify admins
        from Accounts.models import User  
        admins = User.objects.filter(user_type='admin')
        for admin in admins:
            LoanNotification.objects.create(
                user=admin,
                message=f"{request.user.username} applied for a loan of ₦{loan.amount}."
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#Check latest loan status/details
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_loan_status(request):
    loan = Loan.objects.filter(user=request.user).order_by('-created_at').first()
    if not loan:
        return Response({"message": "No loan found."})
    return Response({
        "loan_status": loan.loan_status,
        "amount": float(loan.amount),
        "repayment_plan": loan.repayment_plan,
        "interest": float(loan.interest),
        "total_repayable": float(loan.total_repayable),
        "amount_paid": float(loan.amount_paid),
        "balance": float(loan.balance)
    })


#Approve or Reject a loan 
@api_view(['POST'])
@permission_classes([IsAdminUser])
def update_loan_status(request, loan_id):
    action = request.data.get('action')  # should be 'approve' or 'reject'
    
    if action not in ['approve', 'reject']:
        return Response({"error": "Action must be 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        loan = Loan.objects.get(id=loan_id)

        print("Current loan status:", loan.loan_status)  # Debugging line

        if loan.loan_status.lower() != "pending":
            return Response({"error": "Loan already reviewed."}, status=status.HTTP_400_BAD_REQUEST)

        # Update loan status
        loan.loan_status = 'Accepted' if action == 'approve' else 'Rejected'
        loan.save()

        # Notify member
        LoanNotification.objects.create(user=loan.user, message=f"Loan {loan.loan_status.lower()}.")

        return Response({"message": f"Loan {loan.loan_status} successfully."}, status=status.HTTP_200_OK)

    except Loan.DoesNotExist:
        return Response({"error": "Loan not found."}, status=status.HTTP_404_NOT_FOUND)


# Repay part or full of a loan
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def repay_loan(request, loan_id):
    try:
        loan = Loan.objects.get(id=loan_id, user=request.user)

        if loan.loan_status != 'Accepted':
            return Response({"error": "Loan not approved yet."}, status=status.HTTP_400_BAD_REQUEST)

        if loan.is_repaid:
            return Response({"error": "Loan already fully repaid."}, status=status.HTTP_400_BAD_REQUEST)

        amount = request.data.get('amount')
        if not amount:
            return Response({"error": "Repayment amount required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(amount)
        except:
            return Response({"error": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0 or request.user.balance < amount:
            return Response({"error": "Invalid or insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

        loan.amount_paid += amount

        # Mark as repaid if total met
        if loan.amount_paid >= loan.total_repayable:
            loan.amount_paid = loan.total_repayable
            loan.is_repaid = True
            LoanNotification.objects.create(user=request.user, message="Loan fully repaid.")

        loan.save()

        request.user.balance -= amount
        request.user.save()

        return Response({
            "message": f"₦{amount} payment recorded.",
            "paid": float(loan.amount_paid),
            "remaining": float(loan.balance),
            "loan_status": loan.loan_status
        })
    except Loan.DoesNotExist:
        return Response({"error": "Loan not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_history(request):
    loans = Loan.objects.filter(user=request.user)
    return Response(LoanSerializer(loans, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_summary(request):
    user = request.user
    total_savings = user.savings.aggregate(total=Sum('amount'))['total'] or 0
    latest = Loan.objects.filter(user=user).order_by('-created_at').first()

    loan_info = None
    if latest:
        loan_info = {
            "amount": float(latest.amount),
            "loan_status": latest.loan_status,
            "plan": latest.repayment_plan,
            "interest": float(latest.interest),
            "paid": float(latest.amount_paid),
            "balance": float(latest.balance)
        }

    return Response({
        "username": user.username,
        "balance": float(user.balance),
        "total_savings": float(total_savings),
        "latest_loan": loan_info
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_view_all_loans(request):
    loans = Loan.objects.select_related('user').order_by('-created_at')
    return Response(LoanSerializer(loans, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def repayment_schedule(request, loan_id):
    try:
        loan = Loan.objects.get(id=loan_id, user=request.user)

        if loan.loan_status != "Accepted":
            return Response({"error": "Loan is not approved yet."}, status=status.HTTP_400_BAD_REQUEST)

        months = int(loan.repayment_plan[0])  # '2m', '4m', '6m' — extract number
        total = loan.total_repayable
        per_installment = total / months
        start_date = loan.created_at

        schedule = [
            {
                "installment": i + 1,
                "amount": float(round(per_installment, 2)),
                "due_date": (start_date + timedelta(days=30 * (i + 1))).strftime('%Y-%m-%d')
            }
            for i in range(months)
        ]
        return Response({
            "total_repayable": float(total),
            "per_installment": float(round(per_installment, 2)),
            "schedule": schedule
        })
    except Loan.DoesNotExist:
        return Response({"error": "Loan not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_notifications(request):
    #Fetch all loan notifications for the currently logged-in user (member or admin).
    notifications = LoanNotification.objects.filter(user=request.user).order_by('-created_at')
    data = [
        {
            "message": note.message,
            "timestamp": note.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for note in notifications
    ]
    return Response(data)
