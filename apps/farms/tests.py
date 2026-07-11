"""
Tests for the Farms domain.
Coverage targets: happy path, 401, 403, 400, 404.
Run: pytest apps/farms/tests.py -v --cov=apps/farms
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()


# ── Factories ────────────────────────────────────────────────
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    email = factory.Sequence(lambda n: f"farmer{n}@test.com")
    name = factory.Faker("name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class FarmFactory(DjangoModelFactory):
    class Meta:
        model = "farms.Farm"
    owner = factory.SubFactory(UserFactory)
    name = factory.Faker("company")
    location = factory.Faker("city")


# ── Fixtures ─────────────────────────────────────────────────
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def other_user(db):
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def farm(db, user):
    return FarmFactory(owner=user)


# ── Test: Farm CRUD ──────────────────────────────────────────
@pytest.mark.django_db
class TestFarmList:
    def test_list_requires_auth(self, api_client):
        """401 — anonymous user cannot list farms."""
        url = reverse("farm-list")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_returns_only_own_farms(self, auth_client, farm, other_user):
        """User only sees their own farms — not other users' farms."""
        FarmFactory(owner=other_user)  # another user's farm
        url = reverse("farm-list")
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        # Should only return the authenticated user's farm
        ids = [f["id"] for f in res.data["results"]]
        assert str(farm.id) in ids
        assert len(ids) == 1

    def test_create_farm_success(self, auth_client):
        """201 — valid payload creates a farm."""
        url = reverse("farm-list")
        payload = {"name": "Ansari Maize Farm", "location": "Nakuru"}
        res = auth_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["name"] == "Ansari Maize Farm"

    def test_create_farm_missing_name(self, auth_client):
        """400 — name is required."""
        url = reverse("farm-list")
        res = auth_client.post(url, {"location": "Nakuru"}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in res.data


@pytest.mark.django_db
class TestFarmDetail:
    def test_get_own_farm(self, auth_client, farm):
        """200 — owner can retrieve their farm."""
        url = reverse("farm-detail", kwargs={"pk": farm.id})
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["name"] == farm.name

    def test_get_other_users_farm_forbidden(self, auth_client, other_user):
        """403 — user cannot access another user's farm."""
        other_farm = FarmFactory(owner=other_user)
        url = reverse("farm-detail", kwargs={"pk": other_farm.id})
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_get_nonexistent_farm(self, auth_client):
        """404 — farm does not exist."""
        import uuid
        url = reverse("farm-detail", kwargs={"pk": uuid.uuid4()})
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_404_NOT_FOUND


# ── Test: Auth endpoints ─────────────────────────────────────
@pytest.mark.django_db
class TestAuth:
    def test_register_success(self, api_client):
        """201 — new user registers successfully."""
        url = reverse("register")
        payload = {
            "email": "newfarmer@test.com",
            "password": "securepass123",
            "name": "New Farmer",
            "phone": "0712345678",
        }
        res = api_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert "email" in res.data

    def test_register_duplicate_email(self, api_client, user):
        """400 — duplicate email rejected."""
        url = reverse("register")
        payload = {
            "email": user.email,
            "password": "securepass123",
            "name": "Another Farmer",
        }
        res = api_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self, api_client, user):
        """200 — valid credentials return JWT pair."""
        url = reverse("token-obtain")
        res = api_client.post(
            url, {"email": user.email, "password": "testpass123"}, format="json"
        )
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data
        assert "refresh" in res.data

    def test_login_wrong_password(self, api_client, user):
        """401 — wrong password returns 401."""
        url = reverse("token-obtain")
        res = api_client.post(
            url, {"email": user.email, "password": "wrongpassword"}, format="json"
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
