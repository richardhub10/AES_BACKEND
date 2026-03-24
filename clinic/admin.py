from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
	list_display = ("id", "patient", "doctor_name", "scheduled_for", "status")
	list_filter = ("status",)
	search_fields = ("doctor_name", "patient__username")

# Register your models here.
