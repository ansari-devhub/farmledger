from rest_framework import viewsets, generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.core.permissions import IsFarmOwner, IsPlantingOwner
from apps.farms.models import Season
from .models import PlantingRecord, InputExpense
from .serializers import (
    PlantingRecordReadSerializer,
    PlantingRecordWriteSerializer,
    InputExpenseSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List all planting records (scoped to user)", tags=["Plantings"]),
    create=extend_schema(summary="Record a new planting", tags=["Plantings"]),
    retrieve=extend_schema(summary="Get a planting record", tags=["Plantings"]),
    partial_update=extend_schema(summary="Update a planting record", tags=["Plantings"]),
)
class PlantingRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ["crop", "season"]
    ordering_fields = ["date_planted", "created_at"]

    def get_queryset(self):
        """Only plantings that belong to farms the user owns."""
        return (
            PlantingRecord.objects
            .filter(season__farm__owner=self.request.user)
            .select_related("crop", "season", "season__farm")
            .prefetch_related("expenses")
            .order_by("-date_planted")
        )

    def get_serializer_class(self):
        # Read/write split: different shapes for read vs write
        if self.request.method in ["POST", "PATCH", "PUT"]:
            return PlantingRecordWriteSerializer
        return PlantingRecordReadSerializer

    def get_permissions(self):
        if self.action in ["retrieve", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsPlantingOwner()]
        return [permissions.IsAuthenticated()]


@extend_schema_view(
    list=extend_schema(summary="List input expenses for a planting", tags=["Expenses"]),
    create=extend_schema(summary="Add an input expense", tags=["Expenses"]),
    retrieve=extend_schema(summary="Get an expense", tags=["Expenses"]),
    partial_update=extend_schema(summary="Update an expense", tags=["Expenses"]),
    destroy=extend_schema(summary="Delete an expense", tags=["Expenses"]),
)
class InputExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = InputExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    filterset_fields = ["input_type"]

    def _get_planting(self):
        planting = get_object_or_404(PlantingRecord, pk=self.kwargs["planting_pk"])
        if planting.season.farm.owner != self.request.user:
            raise PermissionDenied("You do not own this planting.")
        return planting

    def get_queryset(self):
        return InputExpense.objects.filter(planting_record=self._get_planting())

    def perform_create(self, serializer):
        serializer.save(planting_record=self._get_planting())
