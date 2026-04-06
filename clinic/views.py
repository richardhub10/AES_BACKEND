from django.contrib.auth import get_user_model

from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Appointment
from .serializers import AppointmentSerializer, RegisterSerializer, StaffUserSerializer


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
	serializer = RegisterSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	user = serializer.save()
	return Response({"id": user.id, "email": user.email, "username": user.username})


@api_view(["GET"])
def me(request):
	user = request.user
	profile = getattr(user, "profile", None)
	return Response(
		{
			"id": user.id,
			"username": user.username,
			"email": user.email,
			"first_name": user.first_name,
			"last_name": user.last_name,
			"birthday": getattr(profile, "birthday", None),
			"school_id": getattr(profile, "school_id", ""),
			"contact_number": getattr(profile, "contact_number", ""),
			"is_staff": user.is_staff,
		}
	)


class IsOwnerOrStaff(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):  # noqa: ANN001
		return request.user and (request.user.is_staff or obj.patient_id == request.user.id)


class AppointmentViewSet(viewsets.ModelViewSet):
	serializer_class = AppointmentSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

	def get_queryset(self):
		user = self.request.user
		if user.is_staff:
			return Appointment.objects.select_related("patient", "patient__profile").all()
		return Appointment.objects.select_related("patient", "patient__profile").filter(patient=user)

	@action(detail=True, methods=["GET"], url_path="decrypt")
	def decrypt(self, request, pk=None):  # noqa: ANN001
		appt = self.get_object()  # enforces IsOwnerOrStaff
		serializer = self.get_serializer(appt, context={"request": request, "return_plaintext": True})
		return Response(serializer.data)


class IsStaffUser(permissions.BasePermission):
	def has_permission(self, request, view):  # noqa: ANN001
		return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class StaffUserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
	"""Staff-only view of registered accounts.

	Supports:
	- GET /api/staff/users/
	- PATCH /api/staff/users/{id}/  (is_active only)
	"""

	serializer_class = StaffUserSerializer
	permission_classes = [permissions.IsAuthenticated, IsStaffUser]

	def get_queryset(self):
		User = get_user_model()
		return User.objects.select_related("profile").all().order_by("-date_joined")

	def partial_update(self, request, *args, **kwargs):  # noqa: ANN001
		# Only allow toggling is_active.
		allowed = {"is_active"}
		extra = set(request.data.keys()) - allowed
		if extra:
			return Response({"detail": "Only 'is_active' can be updated."}, status=400)

		# Prevent staff from deactivating themselves by mistake.
		obj = self.get_object()
		if obj.pk == request.user.pk and request.data.get("is_active") is False:
			return Response({"detail": "You cannot deactivate your own account."}, status=400)

		return super().partial_update(request, *args, **kwargs)
