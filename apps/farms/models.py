from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Farm(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farms",
    )
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.name} ({self.owner.name})"

    class Meta:
        db_table = "farms"
        ordering = ["-created_at"]


class Season(TimeStampedModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="seasons")
    name = models.CharField(max_length=100)  # e.g. "Long Rains 2024"
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} — {self.farm.name}"

    class Meta:
        db_table = "seasons"
        ordering = ["-start_date"]


class Crop(TimeStampedModel):
    """Reference table — shared across all farms (admin-managed)."""
    CROP_TYPES = [
        ("cereal", "Cereal"),
        ("legume", "Legume"),
        ("vegetable", "Vegetable"),
        ("fruit", "Fruit"),
        ("tuber", "Tuber"),
        ("other", "Other"),
    ]
    name = models.CharField(max_length=100, unique=True)
    variety = models.CharField(max_length=100, blank=True)
    crop_type = models.CharField(max_length=20, choices=CROP_TYPES, default="other")

    def __str__(self):
        return f"{self.name} ({self.variety})" if self.variety else self.name

    class Meta:
        db_table = "crops"
        ordering = ["name"]
