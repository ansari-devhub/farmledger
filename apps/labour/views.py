from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.farms.models import Farm
from apps.operations.models import PlantingRecord
from .models import Worker, LabourLog
from .serializers import WorkerSerializer, LabourLogSerializer


@extend_schema_view(
    list=extend_schema(summary="List workers for a farm", tags=["Labour"]),
    create=extend_schema(summary="Add a worker", tags=["Labour"]),
    retrieve=extend_schema(summary="Get a worker", tags=["Labour"]),
    partial_update=extend_schema(summary="Update worker details", tags=["Labour"]),
)
class WorkerViewSet(viewsets.ModelViewSet):
    serializer_class = WorkerSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def _get_farm(self):
        farm = get_object_or_404(Farm, pk=self.kwargs["farm_pk"])
        if farm.owner != self.request.user:
            raise PermissionDenied("You do not own this farm.")
        return farm

    def get_queryset(self):
        return Worker.objects.filter(farm=self._get_farm())

    def perform_create(self, serializer):
        serializer.save(farm=self._get_farm())


@extend_schema_view(
    list=extend_schema(summary="List labour logs for a planting", tags=["Labour"]),
    create=extend_schema(summary="Log a worker's day(s)", tags=["Labour"]),
    retrieve=extend_schema(summary="Get a labour log entry", tags=["Labour"]),
    partial_update=extend_schema(summary="Update a labour log", tags=["Labour"]),
)
class LabourLogViewSet(viewsets.ModelViewSet):
    serializer_class = LabourLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ["task_type", "worker"]
    ordering_fields = ["work_date"]

    def _get_planting(self):
        planting = get_object_or_404(PlantingRecord, pk=self.kwargs["planting_pk"])
        if planting.season.farm.owner != self.request.user:
            raise PermissionDenied("You do not own this planting.")
        return planting

    def get_queryset(self):
        return (
            LabourLog.objects
            .filter(planting_record=self._get_planting())
            .select_related("worker")
        )

    def perform_create(self, serializer):
        serializer.save(planting_record=self._get_planting())
