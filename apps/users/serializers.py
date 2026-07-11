from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    """Write-only: used on POST /auth/register/"""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password", "name", "phone"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserReadSerializer(serializers.ModelSerializer):
    """Read-only: used in responses — never exposes password."""
    class Meta:
        model = User
        fields = ["id", "email", "name", "phone", "created_at"]
        read_only_fields = fields
