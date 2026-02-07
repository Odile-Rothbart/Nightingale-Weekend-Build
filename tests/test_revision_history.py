import pytest
from rest_framework_simplejwt.tokens import RefreshToken
from notes.models import VersionSnapshot, AuditLog

def auth(client, user):
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")

@pytest.mark.django_db
def test_edit_creates_version_snapshot_and_audit(api_client, users, patient, entries):
    staff_note = entries["staff_note"]
    auth(api_client, users["staff"])

    # edit
    resp = api_client.post(f"/api/entries/{staff_note.id}/edit/", {"content": "Staff note: updated"}, format="json")
    assert resp.status_code == 200
    new_version = resp.json()["new_version"]
    assert new_version == 1  # first snapshot is version 1

    snaps = VersionSnapshot.objects.filter(entry=staff_note).order_by("version")
    assert snaps.count() == 1
    assert snaps.first().content == "Staff note: updated"

    audit = AuditLog.objects.filter(patient=patient, action="edit_entry").first()
    assert audit is not None
    assert audit.meta.get("entry_id") == staff_note.id

@pytest.mark.django_db
def test_revert_creates_new_version_and_restores_content(api_client, users, entries):
    staff_note = entries["staff_note"]
    auth(api_client, users["staff"])

    api_client.post(f"/api/entries/{staff_note.id}/edit/", {"content": "v1"}, format="json")
    api_client.post(f"/api/entries/{staff_note.id}/edit/", {"content": "v2"}, format="json")

    # revert to version 1 (content = v1)
    resp = api_client.post(f"/api/entries/{staff_note.id}/revert/1/")
    assert resp.status_code == 200

    staff_note.refresh_from_db()
    assert staff_note.content == "v1"

    # after revert, latest version should be 3
    from notes.models import VersionSnapshot
    latest = VersionSnapshot.objects.filter(entry=staff_note).order_by("-version").first()
    assert latest.version == 3
    assert latest.content == "v1"
