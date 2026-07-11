"""
Abstract base models — DRY timestamps and UUID PKs for every model.
All concrete models inherit from TimeStampedModel.
"""
import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """Provides uuid PK, created_at, updated_at on every model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
