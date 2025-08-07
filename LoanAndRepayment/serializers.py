from rest_framework import serializers
from LoanAndRepayment.models import Loan
from decimal import Decimal

class LoanSerializer(serializers.ModelSerializer):
    # Expose calculated fields as read-only
    interest = serializers.ReadOnlyField()  
    total_repayable = serializers.ReadOnlyField()
    balance = serializers.ReadOnlyField()

    class Meta:
        model = Loan
        fields = [
            'id', 'amount', 'interest', 'repayment_plan', 'created_at',
            'loan_status', 'total_repayable', 'amount_paid', 'balance', 'is_repaid'
        ]
        read_only_fields = [
            'interest', 'loan_status', 'total_repayable', 'created_at',
            'amount_paid', 'balance', 'is_repaid'
        ]

    def validate_amount(self, value):
        if value < 100000:
            raise serializers.ValidationError("Minimum loan amount is ₦100,000")
        return value

    def validate(self, data):
        user = self.context['request'].user
        total_saved = sum([s.amount for s in user.savings.all()])
        if total_saved < 100000:
            raise serializers.ValidationError("You must have saved at least ₦100,000 before applying for a loan.")
        has_active_loan = Loan.objects.filter(
            user=user,
            is_repaid=False,
            loan_status__in=['Pending', 'Approved']  
        ).exists()
        if has_active_loan:
            raise serializers.ValidationError("You already have a pending or active loan.")
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['interest'] = (validated_data['amount'] / Decimal('1000')) * Decimal('10')
        return super().create(validated_data)
