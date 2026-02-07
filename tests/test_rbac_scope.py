import pytest
from rest_framework_simplejwt.tokens import RefreshToken

def auth(client, user):
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")

@pytest.mark.django_db
def test_patient_only_sees_patient_facing_entries(api_client, users, patient, entries):
    auth(api_client, users["pat"])
    resp = api_client.get(f"/api/patients/{patient.id}/care-note/")
    assert resp.status_code == 200
    data = resp.json()

    # patient should not see staff/clinician notes in timeline
    types = {e["type"] for e in data["timeline"]}
    assert "staff_note" not in types
    assert "clinician_note" not in types

    # patient can see ai_patient_session_summary
    assert "ai_patient_session_summary" in types
