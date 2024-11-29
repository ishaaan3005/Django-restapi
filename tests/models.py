from django.db import models
from django.core.validators import MinValueValidator

class TestResult(models.Model):
    patient_id = models.IntegerField(
        validators=[MinValueValidator(1)],
        unique=True,
        null=False
    )
    test_name = models.CharField(
        max_length=100,
        choices=[
            ('GLUCOSE', 'Blood Glucose'),
            ('HB', 'Hemoglobin'),
            ('CHOL', 'Cholesterol')
        ]
    )
    value = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )
    unit = models.CharField(max_length=10)
    test_date = models.DateTimeField()
    is_abnormal = models.BooleanField()

    class Meta:
        indexes = [
            models.Index(fields=['patient_id', 'test_name'])
        ]
