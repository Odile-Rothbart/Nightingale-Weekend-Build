from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ("patient", "patient"),
        ("staff", "staff"),
        ("clinician", "clinician"),
        ("admin", "admin"),
    ]
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="staff")
    clinic_id = models.CharField(max_length=64, null=True, blank=True)
    patient_id = models.IntegerField(null=True, blank=True)
