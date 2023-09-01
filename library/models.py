from django.db import models
from django.utils.translation import gettext_lazy as _


class Book(models.Model):
    class CoverForBook(models.TextChoices):
        HARD = _("Hard")
        SOFT = _("Soft")

    title = models.CharField(max_length=60, unique=True)
    author = models.CharField(max_length=255, unique=True)
    cover = models.CharField(max_length=4, choices=CoverForBook.choices)
    inventory = models.PositiveIntegerField(default=1)
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"Title: {self.title} | Inventory: {self.inventory}"
