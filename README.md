# Nightingale Mini Build — Care Note (Django + DRF + JWT)

A minimal, end-to-end **Care Note** prototype with:
- **Glance View (Highlights)** with provenance (each highlight links to a source timeline entry)
- **Timeline (Entries)** across staff/clinician/system notes
- **RBAC** (patient vs staff/clinician/admin)
- **Revision history + revert**
- **Optimistic concurrency control** (`If-Match` → 409 conflict)
- **Mock AI patient summary** (system-generated entry, no external key required)
- **Automated tests** (pytest)

> Data is **synthetic** for demo/testing.

---

## Tech Stack
- Python 3.9+
- Django
- Django REST Framework
- SimpleJWT (JWT auth)
- pytest + pytest-django

---

## Quick Start

### 1) Create venv & install dependencies
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

python -m pip install -U pip
python -m pip install Django djangorestframework djangorestframework-simplejwt pytest pytest-django python-dotenv
```

### 2) Migrate DB

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3) Create demo users

```bash
python manage.py createsuperuser
python manage.py shell
```

In shell:

```python
from accounts.models import User
User.objects.create_user(username="staff1", password="pass1234", role="staff", clinic_id="clinicA")
User.objects.create_user(username="clin1", password="pass1234", role="clinician", clinic_id="clinicA")
User.objects.create_user(username="pat1",  password="pass1234", role="patient", clinic_id="clinicA")
User.objects.create_user(username="admin1", password="pass1234", role="admin", clinic_id="clinicA")
print("ok")
exit()
```

### 4) Create a synthetic patient + entries

```bash
python manage.py shell
```

```python
from notes.models import Patient, Entry
from accounts.models import User

p = Patient.objects.create(clinic_id="clinicA", display_name="Synthetic Patient A")
staff = User.objects.get(username="staff1")
clin = User.objects.get(username="clin1")
pat = User.objects.get(username="pat1")
pat.patient_id = p.id
pat.save(update_fields=["patient_id"])

Entry.objects.create(
  patient=p, author=staff, author_role="staff", type="staff_note",
  provenance_pointer="manual:staff_note:1",
  content="Staff note: patient reports mild cough for 2 days."
)
Entry.objects.create(
  patient=p, author=clin, author_role="clinician", type="clinician_note",
  provenance_pointer="manual:clinician_note:1",
  content="Clinician note: differential includes viral URI; advise hydration."
)
print("patient_id =", p.id)
exit()
```

### 5) Run server

```bash
python manage.py runserver
```

---

## Web UI (Minimal Frontend)

Open:

* `http://127.0.0.1:8000/patients/<patient_id>/`

Login on the right panel:

* `staff1 / pass1234`
* `clin1 / pass1234`
* `pat1 / pass1234`

Features in UI:

* **Generate Highlights** (creates suggested highlights from non-AI notes and links them to source entries)
* **Accept/Reject** highlights (clinician/admin)
* **Generate Patient Summary (Mock)** (creates a `system` entry of type `ai_patient_session_summary`)

---

## API Endpoints

### Auth (JWT)

* `POST /api/auth/token/` → `{access, refresh}`
* `POST /api/auth/refresh/` → `{access}`

### Care Note

* `GET /api/patients/{patient_id}/care-note/`

  * Returns `{glance: {highlights}, timeline: [entries]}`

### Highlights

* `POST /api/patients/{patient_id}/highlights/generate/`

  * Generates **suggested** highlights (with provenance pointing to an entry/span)
* `POST /api/highlights/{highlight_id}/status/` (clinician/admin)

  * Body: `{"status":"accepted" | "rejected" | "suggested"}`

### Mock Patient Summary

* `POST /api/patients/{patient_id}/ai/patient-summary-mock/`

  * Creates a `system` entry: `type=ai_patient_session_summary`
  * Note: mock summary is stored in the timeline; it is not used as a highlight source.

### Entry Editing (Revision + Concurrency)

* `POST /api/entries/{entry_id}/edit/`

  * Body: `{"content":"..."}`
  * Optional header: `If-Match: <current_version>`
  * Returns 409 if version mismatch
* `GET /api/entries/{entry_id}/versions/`
* `POST /api/entries/{entry_id}/revert/{version}/`

---

## RBAC Rules (MVP)

* **Clinic scope**: non-admin users cannot access patients in a different clinic.
* **Patient**:

  * Can only access `patient_id == user.patient_id`
  * Only sees `ai_patient_session_summary` entries in timeline
  * Only sees **accepted** highlights
  * Cannot generate highlights or summaries; cannot accept/reject
* **Staff/Clinician/Admin**:

  * Can access patients within clinic scope (admin unrestricted)
  * Can view full timeline (MVP)
* **Editing**:

  * staff can edit staff notes; clinician can edit clinician notes; admin can edit all (MVP)

---

## Running Tests

```bash
pytest -q
```

Test coverage includes:

* RBAC filtering
* highlight provenance
* revision history + revert
* optimistic concurrency conflict (409)

---

## Demo Script

1. Login as **staff1** → open `/patients/{id}/`
2. Click **Generate Highlights** → see suggested highlight(s), click “Jump to source”
3. Login as **clin1** → **Accept** a highlight → status becomes `accepted`
4. Login as **pat1** → patient sees only **accepted** highlights and only the patient-facing summary in timeline
5. (Optional) Show concurrency: edit an entry with wrong `If-Match` → 409 conflict
