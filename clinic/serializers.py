from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Appointment


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["username", "password", "first_name", "last_name", "email"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AppointmentSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(source="patient.username", read_only=True)
    doctor_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_username",
            "doctor_name",
            "scheduled_for",
            "reason",
            "notes",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["patient", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["patient"] = request.user
        if not validated_data.get("doctor_name"):
            validated_data["doctor_name"] = "General"
        return super().create(validated_data)

    def validate(self, attrs):
        request = self.context.get("request")
        if not request:
            return attrs

        # For updates: restrict what non-staff users can change.
        if request.method in ("PUT", "PATCH") and not request.user.is_staff:
            allowed = {"reason", "notes", "status"}
            disallowed = set(attrs.keys()) - allowed
            if disallowed:
                raise serializers.ValidationError(
                    {"detail": f"Patients cannot update fields: {sorted(disallowed)}"}
                )

            if "status" in attrs and attrs["status"] != Appointment.Status.CANCELLED:
                raise serializers.ValidationError(
                    {"status": "Patients may only set status to 'cancelled'."}
                )

        return attrs
