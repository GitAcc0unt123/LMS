from django.core.exceptions import ValidationError
from django.utils import timezone

# https://docs.djangoproject.com/en/3.2/ref/validators/
# Field level validation

def validate_datetime_future(value):
    """проверка: datetime.now() <= value"""
    if value < timezone.now():
        raise ValidationError('value < timezone.now() --> datetime must be in the future')
    return value