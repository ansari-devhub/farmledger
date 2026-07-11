from rest_framework import serializers
from .models import Farm, Season, Crop


class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ["id", "name", "location", "created_at"]
        read_only_fields = ["id", "created_at"]


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ["id", "name", "start_date", "end_date", "farm", "created_at"]
        read_only_fields = ["id", "farm", "created_at"]


class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = ["id", "name", "variety", "crop_type"]
        read_only_fields = ["id"]
