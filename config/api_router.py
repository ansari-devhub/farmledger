"""
Central API router — all ViewSets and nested routes registered here.
Nested resources use drf-nested-routers pattern (manual for clarity).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users.views import RegisterView, LoginView, TokenRefreshView
from apps.farms.views import FarmViewSet, SeasonViewSet, CropViewSet
from apps.operations.views import PlantingRecordViewSet, InputExpenseViewSet
from apps.commerce.views import (
    BuyerViewSet,
    HarvestRecordViewSet,
    SaleViewSet,
    PlantingSummaryView,
    FarmDashboardView,
)
from apps.labour.views import WorkerViewSet, LabourLogViewSet

router = DefaultRouter()
router.register(r"farms", FarmViewSet, basename="farm")
router.register(r"crops", CropViewSet, basename="crop")
router.register(r"plantings", PlantingRecordViewSet, basename="planting")

urlpatterns = [
    # ── Auth ────────────────────────────────────────────────────
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/token/", LoginView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # ── Router-registered ViewSets ───────────────────────────────
    path("", include(router.urls)),

    # ── Nested: Farm → Seasons ───────────────────────────────────
    path(
        "farms/<uuid:farm_pk>/seasons/",
        SeasonViewSet.as_view({"get": "list", "post": "create"}),
        name="farm-seasons-list",
    ),
    path(
        "farms/<uuid:farm_pk>/seasons/<uuid:pk>/",
        SeasonViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="farm-seasons-detail",
    ),

    # ── Nested: Farm → Workers ───────────────────────────────────
    path(
        "farms/<uuid:farm_pk>/workers/",
        WorkerViewSet.as_view({"get": "list", "post": "create"}),
        name="farm-workers-list",
    ),
    path(
        "farms/<uuid:farm_pk>/workers/<uuid:pk>/",
        WorkerViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="farm-workers-detail",
    ),

    # ── Nested: Farm → Buyers ────────────────────────────────────
    path(
        "farms/<uuid:farm_pk>/buyers/",
        BuyerViewSet.as_view({"get": "list", "post": "create"}),
        name="farm-buyers-list",
    ),
    path(
        "farms/<uuid:farm_pk>/buyers/<uuid:pk>/",
        BuyerViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="farm-buyers-detail",
    ),

    # ── Nested: Farm → Dashboard ─────────────────────────────────
    path(
        "farms/<uuid:farm_pk>/dashboard/",
        FarmDashboardView.as_view(),
        name="farm-dashboard",
    ),

    # ── Nested: Planting → Expenses ──────────────────────────────
    path(
        "plantings/<uuid:planting_pk>/expenses/",
        InputExpenseViewSet.as_view({"get": "list", "post": "create"}),
        name="planting-expenses-list",
    ),
    path(
        "plantings/<uuid:planting_pk>/expenses/<uuid:pk>/",
        InputExpenseViewSet.as_view({
            "get": "retrieve",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="planting-expenses-detail",
    ),

    # ── Nested: Planting → Harvests ──────────────────────────────
    path(
        "plantings/<uuid:planting_pk>/harvests/",
        HarvestRecordViewSet.as_view({"get": "list", "post": "create"}),
        name="planting-harvests-list",
    ),
    path(
        "plantings/<uuid:planting_pk>/harvests/<uuid:pk>/",
        HarvestRecordViewSet.as_view({"get": "retrieve"}),
        name="planting-harvests-detail",
    ),

    # ── Nested: Planting → Labour ────────────────────────────────
    path(
        "plantings/<uuid:planting_pk>/labour/",
        LabourLogViewSet.as_view({"get": "list", "post": "create"}),
        name="planting-labour-list",
    ),
    path(
        "plantings/<uuid:planting_pk>/labour/<uuid:pk>/",
        LabourLogViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="planting-labour-detail",
    ),

    # ── Nested: Harvest → Sales ──────────────────────────────────
    path(
        "harvests/<uuid:harvest_pk>/sales/",
        SaleViewSet.as_view({"get": "list", "post": "create"}),
        name="harvest-sales-list",
    ),
    path(
        "harvests/<uuid:harvest_pk>/sales/<uuid:pk>/",
        SaleViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="harvest-sales-detail",
    ),

    # ── Analytics ────────────────────────────────────────────────
    path(
        "plantings/<uuid:pk>/summary/",
        PlantingSummaryView.as_view(),
        name="planting-summary",
    ),
]
