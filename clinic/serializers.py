from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, UserProfile


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    birthday = serializers.DateField()
    school_id = serializers.CharField(max_length=64)
    contact_number = serializers.CharField(max_length=32)

    def validate_email(self, value):
        User = get_user_model()
        email_norm = value.strip().lower()
        if User.objects.filter(email__iexact=email_norm).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email_norm

    def create(self, validated_data):
        User = get_user_model()

        password = validated_data.pop("password")
        birthday = validated_data.pop("birthday")
        school_id = validated_data.pop("school_id")
        contact_number = validated_data.pop("contact_number")

        email = validated_data.pop("email").strip().lower()

        # Use email as username for simple email+password login.
        user = User(
            username=email,
            email=email,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        user.set_password(password)
        user.save()

        UserProfile.objects.create(
            user=user,
            birthday=birthday,
            school_id=school_id,
            contact_number=contact_number,
        )

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

    def validate_scheduled_for(self, value):
        """Disallow appointments on Saturday/Sunday (UTC)."""
        if not value:
            return value

        dt = value
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone=timezone.utc)

        dt_utc = dt.astimezone(timezone.utc)
        if dt_utc.weekday() in (5, 6):  # Sat/Sun
            raise serializers.ValidationError(
                "Appointments cannot be scheduled on Saturday or Sunday."
            )

        # Only allow 07:00 through 16:00 UTC (hourly).
        h = dt_utc.hour
        m = dt_utc.minute
        s = dt_utc.second
        if s != 0 or m != 0:
            raise serializers.ValidationError(
                "Appointments must be scheduled on the hour between 07:00 and 16:00 UTC."
            )
        if h < 7 or h > 16:
            raise serializers.ValidationError(
                "Appointments must be scheduled between 07:00 and 16:00 UTC."
            )

        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if not request:
            return attrs

        # Staff can accept/confirm/cancel, but must not create appointments.
        if request.method == "POST" and request.user.is_staff:
            raise serializers.ValidationError(
                {"detail": "Staff accounts cannot create appointments."}
            )

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
