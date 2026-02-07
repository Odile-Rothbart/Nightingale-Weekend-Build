from .models import Entry, Highlight, Patient


def filter_patient_queryset(user, patient: Patient):
    # clinic scope
    if user.role != "admin":
        if user.clinic_id and user.clinic_id != patient.clinic_id:
            raise PermissionError("Cross-clinic access denied")

    # patient can only view patient-facing summaries (we restrict to ai_patient_session_summary for MVP)
    if user.role == "patient":
        if user.patient_id != patient.id:
            raise PermissionError("Patient can only access self")
        allowed_types = {"ai_patient_session_summary"}
        return (
            Entry.objects.filter(patient=patient, type__in=allowed_types)
            .order_by("-created_at")
        )

    # staff/clinician/admin: view all entries for now (later we tighten by type)
    return Entry.objects.filter(patient=patient).order_by("-created_at")


def filter_highlights_queryset(user, patient: Patient):
    # patient sees accepted highlights only (MVP)
    qs = Highlight.objects.filter(patient=patient).order_by("-created_at")
    if user.role == "patient":
        return qs.filter(status="accepted")
    return qs
