from rest_framework import viewsets, generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsFarmOwner
from .models import Farm, Season, Crop
from .serializers import FarmSerializer, SeasonSerializer, CropSerializer


@extend_schema_view(
    list=extend_schema(summary="List my farms", tags=["Farms"]),
    create=extend_schema(summary="Create a farm", tags=["Farms"]),
    retrieve=extend_schema(summary="Get a farm", tags=["Farms"]),
    update=extend_schema(summary="Update a farm", tags=["Farms"]),
    partial_update=extend_schema(summary="Partially update a farm", tags=["Farms"]),
    destroy=extend_schema(summary="Delete a farm", tags=["Farms"]),
)
class FarmViewSet(viewsets.ModelViewSet):
    serializer_class = FarmSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["location"]

    def get_queryset(self):
        # Thin view: delegate filtering to queryset, never raw ORM here
        return Farm.objects.filter(owner=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        # List/Create don't need object-level check
        if self.action in ["list", "create"]:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()


@extend_schema_view(
    list=extend_schema(summary="List seasons for a farm", tags=["Seasons"]),
    create=extend_schema(summary="Create a season", tags=["Seasons"]),
    retrieve=extend_schema(summary="Get a season", tags=["Seasons"]),
    partial_update=extend_schema(summary="Update a season", tags=["Seasons"]),
)
class SeasonViewSet(viewsets.ModelViewSet):
    serializer_class = SeasonSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def _get_farm(self):
        farm = get_object_or_404(Farm, pk=self.kwargs["farm_pk"])
        if farm.owner != self.request.user:
            raise PermissionDenied("You do not own this farm.")
        return farm

    def get_queryset(self):
        return Season.objects.filter(farm=self._get_farm()).order_by("-start_date")

    def perform_create(self, serializer):
        serializer.save(farm=self._get_farm())


@extend_schema_view(
    list=extend_schema(summary="List all crop types", tags=["Reference"]),
    retrieve=extend_schema(summary="Get a crop type", tags=["Reference"]),
)
class CropViewSet(viewsets.ReadOnlyModelViewSet):
    """Reference data — admin-managed, read-only for all authenticated users."""
    queryset = Crop.objects.all().order_by("name")
    serializer_class = CropSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["crop_type"]
