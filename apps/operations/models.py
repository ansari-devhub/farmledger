from django.db import models
from apps.core.models import TimeStampedModel
from apps.farms.models import Season, Crop


class PlantingRecord(TimeStampedModel):
    """The spine of the system — every expense, harvest, and labour log links here."""
    season = models.ForeignKey(Season, on_delete=models.PROTECT, related_name="plantings")
    crop = models.ForeignKey(Crop, on_delete=models.PROTECT, related_name="plantings")
    date_planted = models.DateField()
    field_area_acres = models.DecimalField(max_digits=8, decimal_places=2)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.crop} planted {self.date_planted} ({self.season.farm.name})"

    class Meta:
        db_table = "planting_records"
        ordering = ["-date_planted"]


class InputExpense(TimeStampedModel):
    INPUT_TYPES = [
        ("seed", "Seed"),
        ("fertilizer", "Fertilizer"),
        ("pesticide", "Pesticide"),
        ("herbicide", "Herbicide"),
        ("equipment", "Equipment"),
        ("other", "Other"),
    ]
    planting_record = models.ForeignKey(
        PlantingRecord, on_delete=models.CASCADE, related_name="expenses"
    )
    input_type = models.CharField(max_length=20, choices=INPUT_TYPES)
    item_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=30)  # kg, litres, bags
    amount_ksh = models.DecimalField(max_digits=12, decimal_places=2)
    date_purchased = models.DateField()

    def __str__(self):
        return f"{self.item_name} — KSh {self.amount_ksh}"

    class Meta:
        db_table = "input_expenses"
        ordering = ["-date_purchased"]
