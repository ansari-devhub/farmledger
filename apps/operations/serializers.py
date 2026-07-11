from rest_framework import serializers
from django.db.models import Sum
from .models import PlantingRecord, InputExpense
from apps.farms.serializers import CropSerializer, SeasonSerializer


class InputExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = InputExpense
        fields = [
            "id", "input_type", "item_name", "quantity",
            "unit", "amount_ksh", "date_purchased", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PlantingRecordReadSerializer(serializers.ModelSerializer):
    """Enriched read serializer — includes computed totals."""
    crop = CropSerializer(read_only=True)
    season_name = serializers.CharField(source="season.name", read_only=True)
    total_input_cost_ksh = serializers.SerializerMethodField()

    class Meta:
        model = PlantingRecord
        fields = [
            "id", "crop", "season_name", "date_planted",
            "field_area_acres", "notes", "total_input_cost_ksh", "created_at",
        ]

    def get_total_input_cost_ksh(self, obj):
        result = obj.expenses.aggregate(total=Sum("amount_ksh"))
        return result["total"] or 0


class PlantingRecordWriteSerializer(serializers.ModelSerializer):
    """Write serializer — accepts FK ids only."""
    class Meta:
        model = PlantingRecord
        fields = ["season", "crop", "date_planted", "field_area_acres", "notes"]

    def validate_season(self, season):
        """Ensure the season belongs to a farm the user owns."""
        request = self.context["request"]
        if season.farm.owner != request.user:
            raise serializers.ValidationError("You don't own this farm.")
        return season
