from rest_framework import serializers
from .models import HarvestRecord, Sale, Buyer


class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = ["id", "name", "phone", "location", "created_at"]
        read_only_fields = ["id", "created_at"]


class HarvestRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HarvestRecord
        fields = [
            "id", "harvest_date", "quantity_kg",
            "quality_grade", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SaleReadSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.name", read_only=True)
    total_amount_ksh = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    outstanding_ksh = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Sale
        fields = [
            "id", "buyer", "buyer_name", "sale_date", "kg_sold",
            "price_per_kg_ksh", "total_amount_ksh", "payment_status",
            "amount_paid_ksh", "outstanding_ksh", "payment_date",
        ]


class SaleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = [
            "buyer", "sale_date", "kg_sold", "price_per_kg_ksh",
            "payment_status", "amount_paid_ksh", "payment_date",
        ]

    def validate(self, data):
        # When marking as paid, payment_date is required
        if data.get("payment_status") == "paid" and not data.get("payment_date"):
            raise serializers.ValidationError(
                {"payment_date": "Payment date is required when marking as paid."}
            )
        return data


class PlantingSummarySerializer(serializers.Serializer):
    """Read-only analytics — not a model serializer."""
    planting_id = serializers.UUIDField()
    crop_name = serializers.CharField()
    season_name = serializers.CharField()
    total_input_cost_ksh = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_labour_cost_ksh = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_revenue_ksh = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_profit_ksh = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_debt_ksh = serializers.DecimalField(max_digits=12, decimal_places=2)
