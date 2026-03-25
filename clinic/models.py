from django.conf import settings
from django.db import models

from .crypto import decrypt_str, encrypt_str


class EncryptedTextField(models.TextField):
	"""Stores encrypted ciphertext in DB, returns plaintext in Python."""

	def from_db_value(self, value, expression, connection):  # noqa: ANN001
		if value is None:
			return value
		return decrypt_str(value)

	def to_python(self, value):  # noqa: ANN001
		if value is None:
			return value
		if isinstance(value, str):
			return decrypt_str(value)
		return value

	def get_prep_value(self, value):  # noqa: ANN001
		value = super().get_prep_value(value)
		if value is None:
			return value
		return encrypt_str(value)


class Appointment(models.Model):
	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		CONFIRMED = "confirmed", "Confirmed"
		CANCELLED = "cancelled", "Cancelled"

	patient = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="appointments",
	)
	doctor_name = models.CharField(max_length=120)
	scheduled_for = models.DateTimeField()
	reason = EncryptedTextField(blank=True, default="")
	notes = EncryptedTextField(blank=True, default="")
	status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-scheduled_for"]

	def __str__(self) -> str:
		return f"Appointment({self.patient_id}, {self.doctor_name}, {self.scheduled_for})"


class UserProfile(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="profile",
	)
	birthday = models.DateField(null=True, blank=True)
	school_id = models.CharField(max_length=64, blank=True, default="")
	contact_number = models.CharField(max_length=32, blank=True, default="")

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"UserProfile({self.user_id})"
