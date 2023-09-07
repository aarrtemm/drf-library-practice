from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from library.models import Book
from library_service import settings


def validate_future_date(value):
    if value < datetime.now().date():
        raise ValidationError("Date cannot be in the past.")


class Borrowing(models.Model):
    borrow_date = models.DateField(
        auto_now_add=True,
        validators=[validate_future_date],
    )
    expected_return_date = models.DateField(
        validators=[validate_future_date],
        default=timezone.now() + timezone.timedelta(days=7),
    )
    actual_return_date = models.DateField(
        null=True, blank=True, validators=[validate_future_date]
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowing")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowing"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} | {self.book} | {self.borrow_date}"
