from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User
from django.utils import timezone
from datetime import datetime

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=12, min_length=8, write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(max_length=12, min_length=8, write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model= User
        fields =[
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "user_type",
            "password",
            "password2",
            "lock_duration",
            ]
        read_only_fields = ["id","balance", "lock_start", "is_locked",]
        extra_kwargs = {
            'email':    {'required': True},
            'phone_number':    {'required': True},
            'user_type':{'read_only': True},  # enforced to "member"
            'balance':  {'read_only': True},
            'lock_start': {'read_only': True},
            'is_locked': {'read_only': True},
        }
        
    def validate(self,attrs):
        password=attrs.get('password','')
        password2=attrs.get('password2','')
        if password != password2:
            raise serializers.ValidationError("PASSWORD DO NOT MATCH")
        return attrs

    def validate_phone_number(self, value):    # Ensure exactly 11 digits
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError("Phone number must be 11 digits.")
        return value


    def create(self, validated_data):
        validated_data.pop('password2') #Password2 is not needed for creating the user, so we remove it from the data before use.

        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number'],
            address=validated_data['address'],
            user_type='member',  # force it to be a member
            lock_duration=validated_data['lock_duration'],
            balance=10000.00, #Set initial balance to 10,000
            lock_start=timezone.now(), #Set lock start time as now
            is_locked=True,
        )
        user.set_password(validated_data['password'])  #Set up password
        user.save()
        return user