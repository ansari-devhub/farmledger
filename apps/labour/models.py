from django.db import models
from apps.core.models import TimeStampedModel
from apps.farms.models import Farm
from apps.operations.models import PlantingRecord


class Worker(TimeStampedModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="workers")
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    daily_rate_ksh = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "workers"
        ordering = ["name"]


class LabourLog(TimeStampedModel):
    TASK_TYPES = [
        ("planting", "Planting"),
        ("weeding", "Weeding"),
        ("spraying", "Spraying"),
        ("harvesting", "Harvesting"),
        ("transport", "Transport"),
        ("other", "Other"),
    ]
    planting_record = models.ForeignKey(
        PlantingRecord, on_delete=models.CASCADE, related_name="labour_logs"
    )
    worker = models.ForeignKey(Worker, on_delete=models.PROTECT, related_name="logs")
    work_date = models.DateField()
    days_worked = models.DecimalField(max_digits=4, decimal_places=1, default=1)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default="other")
    # Override default rate if agreed rate differs
    total_pay_ksh = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.worker.name} — {self.days_worked} days — KSh {self.total_pay_ksh}"

    class Meta:
        db_table = "labour_logs"
        ordering = ["-work_date"]
