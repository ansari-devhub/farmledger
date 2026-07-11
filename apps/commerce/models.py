from django.db import models
from apps.core.models import TimeStampedModel
from apps.operations.models import PlantingRecord
from apps.farms.models import Farm


class Buyer(TimeStampedModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="buyers")
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "buyers"
        ordering = ["name"]


class HarvestRecord(TimeStampedModel):
    QUALITY_CHOICES = [
        ("grade_a", "Grade A"),
        ("grade_b", "Grade B"),
        ("grade_c", "Grade C"),
        ("mixed", "Mixed"),
    ]
    planting_record = models.ForeignKey(
        PlantingRecord, on_delete=models.PROTECT, related_name="harvests"
    )
    harvest_date = models.DateField()
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    quality_grade = models.CharField(max_length=10, choices=QUALITY_CHOICES, default="grade_a")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.quantity_kg}kg harvested {self.harvest_date}"

    class Meta:
        db_table = "harvest_records"
        ordering = ["-harvest_date"]


class Sale(TimeStampedModel):
    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("partial", "Partial"),
        ("paid", "Paid"),
    ]
    harvest_record = models.ForeignKey(
        HarvestRecord, on_delete=models.PROTECT, related_name="sales"
    )
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, related_name="purchases")
    sale_date = models.DateField()
    kg_sold = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg_ksh = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default="pending")
    amount_paid_ksh = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)

    @property
    def total_amount_ksh(self):
        return self.kg_sold * self.price_per_kg_ksh

    @property
    def outstanding_ksh(self):
        return self.total_amount_ksh - self.amount_paid_ksh

    def __str__(self):
        return f"Sale to {self.buyer.name} — KSh {self.total_amount_ksh}"

    class Meta:
        db_table = "sales"
        ordering = ["-sale_date"]
