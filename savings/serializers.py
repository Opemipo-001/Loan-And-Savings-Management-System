from rest_framework import serializers
from .models import Savings
from datetime import timedelta
from Accounts.models import DURATION_MAP
from django.utils import timezone
from decimal import Decimal

class SavingSerializer(serializers.ModelSerializer):
    lock_duration = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Savings
        fields = [
            'id', 'amount', 'lock_duration', 'created_at',
            'unlock_time', 'interest_credited', 'is_withdrawn'
        ]
        read_only_fields = [
            'created_at', 'unlock_time', 'interest_credited',
            'is_withdrawn', 'lock_duration'
        ]

    def get_lock_duration(self, obj):
        return obj.user.lock_duration

    def validate_amount(self, value):
        if value < 100000:
            raise serializers.ValidationError("Minimum saving amount is ₦100,000")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user

        # Use the user's lock_duration from profile
        lock_duration = user.lock_duration
        validated_data['lock_duration'] = lock_duration

        # Calculate unlock time
        unlock_time = timezone.now() + DURATION_MAP.get(lock_duration, timedelta(0))
        validated_data['unlock_time'] = unlock_time

        # Create the savings record
        saving = super().create(validated_data)

        # Update user balance immediately after saving
        user.balance += saving.amount
        user.save()

        return saving





