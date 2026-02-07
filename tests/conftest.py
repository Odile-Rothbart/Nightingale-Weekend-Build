import pytest
from rest_framework.test import APIClient
from accounts.models import User
from notes.models import Patient, Entry

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def users(db):
    staff = User.objects.create_user(username="staff1", password="pass1234", role="staff", clinic_id="clinicA")
    clin = User.objects.create_user(username="clin1", password="pass1234", role="clinician", clinic_id="clinicA")
    pat = User.objects.create_user(username="pat1", password="pass1234", role="patient", clinic_id="clinicA")
    admin = User.objects.create_user(username="admin1", password="pass1234", role="admin", clinic_id="clinicA")
    return {"staff": staff, "clin": clin, "pat": pat, "admin": admin}

@pytest.fixture
def patient(db, users):
    p = Patient.objects.create(clinic_id="clinicA", display_name="Synthetic Patient A")
    users["pat"].patient_id = p.id
    users["pat"].save(update_fields=["patient_id"])
    return p


@pytest.fixture
def entries(db, users, patient):
    staff_note = Entry.objects.create(
        patient=patient,
        author=users["staff"],
        author_role="staff",
        type="staff_note",
        provenance_pointer="manual:staff_note:1",
        content="Staff note: baseline",
    )
    clin_note = Entry.objects.create(
        patient=patient,
        author=users["clin"],
        author_role="clinician",
        type="clinician_note",
        provenance_pointer="manual:clinician_note:1",
        content="Clin note: baseline",
    )
    ai_patient = Entry.objects.create(
        patient=patient,
        author=None,
        author_role="system",
        type="ai_patient_session_summary",
        provenance_pointer="session:xyz",
        content="Patient-facing summary: baseline",
    )
    return {"staff_note": staff_note, "clin_note": clin_note, "ai_patient": ai_patient}
