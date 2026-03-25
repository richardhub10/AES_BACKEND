from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Allow logging in with either `email`+`password` or `username`+`password`."""

    email = serializers.EmailField(required=False)

    def validate(self, attrs):
        email = (attrs.get("email") or "").strip()

        # If email is provided, translate it into the configured username field.
        if email and not attrs.get(self.username_field):
            User = get_user_model()
            user = User.objects.filter(email__iexact=email).only(self.username_field).first()
            if user is not None:
                attrs[self.username_field] = getattr(user, self.username_field)
            else:
                # Fallback: some installations use email as username.
                attrs[self.username_field] = email

        return super().validate(attrs)


class EmailOrUsernameTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainPairSerializer
