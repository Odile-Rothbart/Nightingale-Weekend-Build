from django.db import models
from django.conf import settings


class Patient(models.Model):
    clinic_id = models.CharField(max_length=64)
    display_name = models.CharField(max_length=128)  # synthetic only

    def __str__(self):
        return f"{self.display_name} ({self.clinic_id})"


class Entry(models.Model):
    ROLE_CHOICES = [
        ("patient", "patient"),
        ("staff", "staff"),
        ("clinician", "clinician"),
        ("system", "system"),
    ]

    TYPE_CHOICES = [
        ("staff_note", "staff_note"),
        ("clinician_note", "clinician_note"),
        ("ai_doctor_consult_summary", "ai_doctor_consult_summary"),
        ("ai_nurse_consult_summary", "ai_nurse_consult_summary"),
        ("ai_patient_session_summary", "ai_patient_session_summary"),
        ("system_event", "system_event"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="entries")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    author_role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    type = models.CharField(max_length=64, choices=TYPE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # must support provenance tracing
    provenance_pointer = models.CharField(max_length=256)

    content = models.TextField()

    def __str__(self):
        return f"{self.patient_id} {self.type} {self.created_at}"


class CommentThread(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="threads")
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    thread = models.ForeignKey(CommentThread, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    author_role = models.CharField(max_length=16)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Highlight(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="highlights")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    text = models.CharField(max_length=256)
    risk_reason = models.CharField(max_length=256)

    # provenance: must link to timeline entry/span
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    span_start = models.IntegerField(default=0)
    span_end = models.IntegerField(default=0)

    status = models.CharField(max_length=16, default="suggested")  # suggested/accepted/rejected


class VersionSnapshot(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="versions")
    version = models.IntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)


class AuditLog(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64)
    meta = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
