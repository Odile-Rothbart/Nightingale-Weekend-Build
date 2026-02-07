from django.urls import path
from .views import CareNoteView, EntryEditView, EntryVersionsView, EntryRevertView, GenerateHighlightsView, HighlightStatusView, GenerateMockPatientSummaryView

urlpatterns = [
    path("patients/<int:patient_id>/care-note/", CareNoteView.as_view(), name="care_note"),
    path("patients/<int:patient_id>/highlights/generate/", GenerateHighlightsView.as_view(), name="gen_highlights"),
    path("entries/<int:entry_id>/edit/", EntryEditView.as_view(), name="entry_edit"),
    path("entries/<int:entry_id>/versions/", EntryVersionsView.as_view(), name="entry_versions"),
    path("entries/<int:entry_id>/revert/<int:version>/", EntryRevertView.as_view(), name="entry_revert"),
    path("highlights/<int:highlight_id>/status/", HighlightStatusView.as_view(), name="highlight_status"),
    path("patients/<int:patient_id>/ai/patient-summary-mock/", GenerateMockPatientSummaryView.as_view(), name="mock_patient_summary"),
]
