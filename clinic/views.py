from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Appointment
from .serializers import AppointmentSerializer, RegisterSerializer


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
			return Appointment.objects.select_related("patient").all()
		return Appointment.objects.select_related("patient").filter(patient=user)
