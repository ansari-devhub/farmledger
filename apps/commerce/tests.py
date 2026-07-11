"""
Analytics endpoint tests — verifies the P&L summary is accurate.
"""
import pytest
import decimal
from django.urls import reverse
from rest_framework import status
from apps.farms.tests import UserFactory, FarmFactory
from factory.django import DjangoModelFactory
import factory


class SeasonFactory(DjangoModelFactory):
    class Meta:
        model = "farms.Season"
    farm = factory.SubFactory(FarmFactory)
    name = "Long Rains 2024"
    start_date = "2024-03-01"
    end_date = "2024-07-31"


class CropFactory(DjangoModelFactory):
    class Meta:
        model = "farms.Crop"
        django_get_or_create = ["name"]
    name = "Maize"
    crop_type = "cereal"


class PlantingFactory(DjangoModelFactory):
    class Meta:
        model = "operations.PlantingRecord"
    season = factory.SubFactory(SeasonFactory)
    crop = factory.SubFactory(CropFactory)
    date_planted = "2024-03-15"
    field_area_acres = decimal.Decimal("2.5")


class ExpenseFactory(DjangoModelFactory):
    class Meta:
        model = "operations.InputExpense"
    planting_record = factory.SubFactory(PlantingFactory)
    input_type = "seed"
    item_name = "H614D Maize Seed"
    quantity = decimal.Decimal("10")
    unit = "kg"
    amount_ksh = decimal.Decimal("3000.00")
    date_purchased = "2024-03-10"


class HarvestFactory(DjangoModelFactory):
    class Meta:
        model = "commerce.HarvestRecord"
    planting_record = factory.SubFactory(PlantingFactory)
    harvest_date = "2024-07-20"
    quantity_kg = decimal.Decimal("800")
    quality_grade = "grade_a"


class BuyerFactory(DjangoModelFactory):
    class Meta:
        model = "commerce.Buyer"
    farm = factory.LazyAttribute(lambda o: o.factory_parent.harvest_record.planting_record.season.farm)
    name = factory.Faker("name")


@pytest.mark.django_db
class TestPlantingSummary:
    def test_summary_calculates_profit_correctly(self, api_client):
        """
        Full integration: plant → add expense → harvest → sell → check P&L.
        Input cost: KSh 3,000
        Revenue: 800kg × 50 = KSh 40,000
        Expected profit: KSh 37,000
        """
        from apps.commerce.models import Buyer, Sale

        user = UserFactory()
        api_client.force_authenticate(user=user)

        farm = FarmFactory(owner=user)
        season = SeasonFactory(farm=farm)
        crop = CropFactory()
        planting = PlantingFactory(season=season, crop=crop)

        # Add an input expense
        ExpenseFactory(planting_record=planting, amount_ksh=decimal.Decimal("3000.00"))

        # Record a harvest
        harvest = HarvestFactory(planting_record=planting)

        # Record a fully paid sale
        buyer = Buyer.objects.create(farm=farm, name="Nairobi Buyer", phone="0700111222")
        Sale.objects.create(
            harvest_record=harvest,
            buyer=buyer,
            sale_date="2024-07-25",
            kg_sold=decimal.Decimal("800"),
            price_per_kg_ksh=decimal.Decimal("50"),
            payment_status="paid",
            amount_paid_ksh=decimal.Decimal("40000.00"),
            payment_date="2024-07-26",
        )

        url = reverse("planting-summary", kwargs={"pk": planting.id})
        res = api_client.get(url)

        assert res.status_code == status.HTTP_200_OK
        assert decimal.Decimal(res.data["total_input_cost_ksh"]) == decimal.Decimal("3000.00")
        assert decimal.Decimal(res.data["total_revenue_ksh"]) == decimal.Decimal("40000.00")
        assert decimal.Decimal(res.data["net_profit_ksh"]) == decimal.Decimal("37000.00")
        assert decimal.Decimal(res.data["outstanding_debt_ksh"]) == decimal.Decimal("0.00")

    def test_summary_forbidden_for_non_owner(self, api_client):
        """403 — another user cannot see summary for someone else's planting."""
        user = UserFactory()
        other = UserFactory()
        api_client.force_authenticate(user=other)

        farm = FarmFactory(owner=user)
        season = SeasonFactory(farm=farm)
        planting = PlantingFactory(season=season)

        url = reverse("planting-summary", kwargs={"pk": planting.id})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_403_FORBIDDEN
