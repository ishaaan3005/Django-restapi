from rest_framework import serializers
from .models import TestResult

class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = ['patient_id', 'test_name', 'value', 'unit', 'test_date', 'is_abnormal']

    def validate_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Test result value must be greater than zero.")
        return value
