from django.shortcuts import render
from .serializers import UserRegistrationSerializer
from .models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework import generics, permissions
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

# Create Your Views here
@api_view(['POST'])  
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User registered successfully as member."}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({"error": "Please provide both username and password."}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user:
        Token.objects.filter(user=user).delete()  # One-session login
        token = Token.objects.create(user=user)
        return Response({"token": token.key}, status=status.HTTP_200_OK)

    return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)


# ADMIN VIEW SPECIFIC USER PROFILE
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def view_user_profile(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        serializer = UserRegistrationSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    try:
        request.user.auth_token.delete()
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_members(request):
    members = User.objects.filter(user_type='member')
    serializer = UserRegistrationSerializer(members, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# FORGOT PASSWORD FUNCTIONALITY
# Request Password Reset
@api_view(['POST'])
def forget_password(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"http://127.0.0.1:8000/reset-password/{uid}/{token}/" #encodes the user's ID (primary key) in base64 format for use in a URL.

        #Sends an email to the user with a message containing the password reset link.
        send_mail(
            'Password Reset Request',
            f'Hello {user.username}, click the link below to reset your password:\n{reset_link}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return Response({'message': 'Password reset email sent.'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'No user with this email.'}, status=status.HTTP_404_NOT_FOUND)


# Step 2: Reset Password Using Token
@api_view(['POST'])
def reset_password(request, uidb64, token):   #This view takes the encoded user ID (uidb64) and the token from the reset link.
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('new_password')
        if not new_password:
            return Response({'error': 'New password is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)
