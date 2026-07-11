from rest_framework import viewsets, generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, extend_schema_view
import decimal

from apps.core.permissions import IsFarmOwner
from apps.operations.models import PlantingRecord
from apps.farms.models import Farm
from .models import HarvestRecord, Sale, Buyer
from .serializers import (
    HarvestRecordSerializer,
    SaleReadSerializer,
    SaleWriteSerializer,
    BuyerSerializer,
    PlantingSummarySerializer,
)

ZERO = decimal.Decimal("0.00")


@extend_schema_view(
    list=extend_schema(summary="List buyers for a farm", tags=["Buyers"]),
    create=extend_schema(summary="Add a buyer", tags=["Buyers"]),
    retrieve=extend_schema(summary="Get a buyer", tags=["Buyers"]),
    partial_update=extend_schema(summary="Update a buyer", tags=["Buyers"]),
)
class BuyerViewSet(viewsets.ModelViewSet):
    serializer_class = BuyerSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def _get_farm(self):
        farm = get_object_or_404(Farm, pk=self.kwargs["farm_pk"])
        if farm.owner != self.request.user:
            raise PermissionDenied("You do not own this farm.")
        return farm

    def get_queryset(self):
        return Buyer.objects.filter(farm=self._get_farm())

    def perform_create(self, serializer):
        serializer.save(farm=self._get_farm())


@extend_schema_view(
    list=extend_schema(summary="List harvests for a planting", tags=["Harvests"]),
    create=extend_schema(summary="Record a harvest", tags=["Harvests"]),
    retrieve=extend_schema(summary="Get a harvest record", tags=["Harvests"]),
)
class HarvestRecordViewSet(viewsets.ModelViewSet):
    serializer_class = HarvestRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def _get_planting(self):
        planting = get_object_or_404(PlantingRecord, pk=self.kwargs["planting_pk"])
        if planting.season.farm.owner != self.request.user:
            raise PermissionDenied("You do not own this planting.")
        return planting

    def get_queryset(self):
        return HarvestRecord.objects.filter(planting_record=self._get_planting())

    def perform_create(self, serializer):
        serializer.save(planting_record=self._get_planting())


@extend_schema_view(
    list=extend_schema(summary="List sales for a harvest", tags=["Sales"]),
    create=extend_schema(summary="Record a sale", tags=["Sales"]),
    retrieve=extend_schema(summary="Get a sale", tags=["Sales"]),
    partial_update=extend_schema(summary="Update payment status", tags=["Sales"]),
)
class SaleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def _get_harvest(self):
        harvest = get_object_or_404(HarvestRecord, pk=self.kwargs["harvest_pk"])
        if harvest.planting_record.season.farm.owner != self.request.user:
            raise PermissionDenied("You do not own this harvest.")
        return harvest

    def get_queryset(self):
        return (
            Sale.objects
            .filter(harvest_record=self._get_harvest())
            .select_related("buyer")
        )

    def get_serializer_class(self):
        if self.request.method in ["POST", "PATCH"]:
            return SaleWriteSerializer
        return SaleReadSerializer

    def perform_create(self, serializer):
        serializer.save(harvest_record=self._get_harvest())


@extend_schema(
    summary="Profit/loss summary for a single planting",
    responses={200: PlantingSummarySerializer},
    tags=["Analytics"],
)
class PlantingSummaryView(generics.RetrieveAPIView):
    """
    The answer to the farmer's core question: 'Did I make money on this crop?'
    Cached for 15 minutes — invalidated by signals on sale/expense changes.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PlantingSummarySerializer

    def get_object(self):
        planting = get_object_or_404(PlantingRecord, pk=self.kwargs["pk"])
        if planting.season.farm.owner != self.request.user:
            raise PermissionDenied("You do not own this planting.")
        return planting

    def retrieve(self, request, *args, **kwargs):
        planting = self.get_object()
        cache_key = f"planting_summary_{planting.id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        # ── Aggregate in the DB — no Python loops ──
        input_cost = planting.expenses.aggregate(
            total=Coalesce(Sum("amount_ksh"), ZERO, output_field=DecimalField())
        )["total"]

        labour_cost = planting.labour_logs.aggregate(
            total=Coalesce(Sum("total_pay_ksh"), ZERO, output_field=DecimalField())
        )["total"]

        # Revenue: kg_sold × price_per_kg across all harvests → all sales
        sales_qs = Sale.objects.filter(
            harvest_record__planting_record=planting
        )
        revenue = sales_qs.aggregate(
            total=Coalesce(
                Sum("amount_paid_ksh"), ZERO, output_field=DecimalField()
            )
        )["total"]

        outstanding = sales_qs.filter(
            payment_status__in=["pending", "partial"]
        ).aggregate(
            total=Coalesce(
                Sum("kg_sold") * Sum("price_per_kg_ksh"), ZERO,
                output_field=DecimalField()
            )
        )["total"] or ZERO

        # Simpler outstanding calc: sum(total) - sum(paid)
        total_billed = sum(
            s.kg_sold * s.price_per_kg_ksh for s in sales_qs
        )
        total_paid = sales_qs.aggregate(
            total=Coalesce(Sum("amount_paid_ksh"), ZERO, output_field=DecimalField())
        )["total"]
        outstanding = total_billed - total_paid

        data = {
            "planting_id": planting.id,
            "crop_name": planting.crop.name,
            "season_name": planting.season.name,
            "total_input_cost_ksh": input_cost,
            "total_labour_cost_ksh": labour_cost,
            "total_revenue_ksh": revenue,
            "net_profit_ksh": revenue - input_cost - labour_cost,
            "outstanding_debt_ksh": outstanding,
        }

        cache.set(cache_key, data, timeout=60 * 15)
        return Response(data)


@extend_schema(
    summary="Farm dashboard — season overview and unpaid buyers",
    tags=["Analytics"],
)
class FarmDashboardView(generics.RetrieveAPIView):
    """
    Top-level summary per farm across all seasons or a specific one.
    Cached aggressively — this is the most expensive query.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        farm = get_object_or_404(Farm, pk=kwargs["farm_pk"])
        if farm.owner != request.user:
            raise PermissionDenied("You do not own this farm.")

        cache_key = f"farm_dashboard_{farm.id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        plantings = PlantingRecord.objects.filter(season__farm=farm)

        total_input = InputExpense_agg(plantings)
        total_labour = LabourLog_agg(plantings)
        total_revenue = Sale.objects.filter(
            harvest_record__planting_record__in=plantings
        ).aggregate(
            total=Coalesce(Sum("amount_paid_ksh"), ZERO, output_field=DecimalField())
        )["total"]

        # Who still owes money?
        from apps.commerce.models import Sale as SaleModel
        from apps.labour.models import LabourLog
        buyers_owing = (
            SaleModel.objects
            .filter(
                harvest_record__planting_record__in=plantings,
                payment_status__in=["pending", "partial"],
            )
            .values("buyer__name", "buyer_id")
            .annotate(amount_owed=Sum("kg_sold"))
            .order_by("-amount_owed")
        )

        data = {
            "farm_name": farm.name,
            "total_spend_ksh": str(total_input + total_labour),
            "total_revenue_ksh": str(total_revenue),
            "net_profit_ksh": str(total_revenue - total_input - total_labour),
            "buyers_owing": list(buyers_owing),
        }

        cache.set(cache_key, data, timeout=60 * 15)
        return Response(data)


def InputExpense_agg(plantings):
    from apps.operations.models import InputExpense
    return InputExpense.objects.filter(
        planting_record__in=plantings
    ).aggregate(
        total=Coalesce(Sum("amount_ksh"), ZERO, output_field=DecimalField())
    )["total"]


def LabourLog_agg(plantings):
    from apps.labour.models import LabourLog
    return LabourLog.objects.filter(
        planting_record__in=plantings
    ).aggregate(
        total=Coalesce(Sum("total_pay_ksh"), ZERO, output_field=DecimalField())
    )["total"]
