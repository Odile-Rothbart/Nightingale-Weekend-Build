import pytest
from rest_framework_simplejwt.tokens import RefreshToken
from notes.editing import get_latest_version

def auth(client, user):
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")

@pytest.mark.django_db
def test_if_match_conflict_returns_409(api_client, users, entries):
    staff_note = entries["staff_note"]
    auth(api_client, users["staff"])

    # current version should be 0 initially
    assert get_latest_version(staff_note) == 0

    # send wrong If-Match
    resp = api_client.post(
        f"/api/entries/{staff_note.id}/edit/",
        {"content": "new content"},
        format="json",
        HTTP_IF_MATCH="999",
    )
    assert resp.status_code == 409
    assert "current_version" in resp.json()
