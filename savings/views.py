from django.shortcuts import render
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from .models import Savings, Notification
from .serializers import SavingSerializer
from Accounts.models import User  


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_saving(request):
    serializer = SavingSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def savings_history(request):
    savings = Savings.objects.filter(user=request.user)
    for s in savings:
        s.check_unlock_status()
    serializer = SavingSerializer(savings, many=True)
    return Response(serializer.data)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Savings

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_saving(request, pk):
    try:
        saving = Savings.objects.get(pk=pk, user=request.user)

        if saving.is_withdrawn:
            return Response({"error": "This savings has already been withdrawn."}, status=status.HTTP_400_BAD_REQUEST)

        if not saving.can_withdraw:
            return Response({"error": "This savings is still locked. Please wait for the lock duration to end."}, status=status.HTTP_400_BAD_REQUEST)

        # Proceed to withdraw
        saving.is_withdrawn = True
        saving.save()

        request.user.balance += saving.amount
        request.user.save()

        return Response({"message": f"₦{saving.amount} has been withdrawn to your account."}, status=status.HTTP_200_OK)

    except Savings.DoesNotExist:
        return Response({"error": "Saving not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user
    user_savings = Savings.objects.filter(user=user)

    total_saved = 0
    total_interest = 0
    pending_interest = 0

    for saving in user_savings:
        saving.check_unlock_status()
        total_saved += saving.amount
        interest = saving.calculate_interest()

        if timezone.now() >= saving.unlock_time:
            total_interest += interest
        else:
            pending_interest += interest

    dashboard_data = {
        "username": user.username,
        "email": user.email,
        "balance": float(user.balance),
        "total_saved": float(total_saved),
        "total_interest_earned": float(total_interest),
        "pending_interest": float(pending_interest),
        "savings_history": SavingSerializer(user_savings, many=True).data
    }

    if user.user_type == "admin":
        all_savings = Savings.objects.all()
        dashboard_data["all_users_savings"] = SavingSerializer(all_savings, many=True).data

    return Response(dashboard_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def read_notification(request, pk):
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        if not notification.read:
            notification.read = True
            notification.save()
        return Response({
            "message": notification.message,
            "created_at": notification.created_at,
            "read": notification.read
        }, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
