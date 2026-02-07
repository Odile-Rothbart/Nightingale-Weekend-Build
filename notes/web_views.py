from django.shortcuts import render, get_object_or_404
from .models import Patient

def patient_page(request, patient_id: int):
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, "care_note.html", {"patient": patient})
