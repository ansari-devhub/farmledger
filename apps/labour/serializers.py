from rest_framework import serializers
from .models import Worker, LabourLog


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ["id", "name", "phone", "daily_rate_ksh", "created_at"]
        read_only_fields = ["id", "created_at"]


class LabourLogSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source="worker.name", read_only=True)

    class Meta:
        model = LabourLog
        fields = [
            "id", "worker", "worker_name", "work_date",
            "days_worked", "task_type", "total_pay_ksh", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
