from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, me, register

router = DefaultRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("auth/register/", register, name="register"),
    path("auth/me/", me, name="me"),
    path("", include(router.urls)),
]
