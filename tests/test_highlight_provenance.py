import pytest
from rest_framework_simplejwt.tokens import RefreshToken
from notes.models import Highlight, Entry, Patient

def auth(client, user):
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")

@pytest.mark.django_db
def test_highlight_has_provenance_pointer_to_entry(api_client, users, patient, entries):
    # Create an entry with a risk keyword
    Entry.objects.create(
        patient=patient,
        author=users["staff"],
        author_role="staff",
        type="staff_note",
        provenance_pointer="manual:risk",
        content="Staff note: chest pain reported.",
    )

    auth(api_client, users["staff"])
    resp = api_client.post(f"/api/patients/{patient.id}/highlights/generate/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] >= 1

    # verify each created highlight points to an existing entry
    for h in data["highlights"]:
        entry_id = h["entry_id"]
        assert Entry.objects.filter(id=entry_id, patient=patient).exists()

@pytest.mark.django_db
def test_patient_sees_only_accepted_highlights(api_client, users, patient, entries):
    # create a suggested highlight and an accepted highlight
    e = entries["ai_patient"]
    Highlight.objects.create(
        patient=patient,
        created_by=users["staff"],
        text="suggested hl",
        risk_reason="reason",
        entry=e,
        span_start=0,
        span_end=5,
        status="suggested",
    )
    Highlight.objects.create(
        patient=patient,
        created_by=users["staff"],
        text="accepted hl",
        risk_reason="reason",
        entry=e,
        span_start=0,
        span_end=5,
        status="accepted",
    )

    auth(api_client, users["pat"])
    resp = api_client.get(f"/api/patients/{patient.id}/care-note/")
    assert resp.status_code == 200
    highlights = resp.json()["glance"]["highlights"]
    texts = {h["text"] for h in highlights}
    assert "accepted hl" in texts
    assert "suggested hl" not in texts
