from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Patient
from .serializers import EntrySerializer, HighlightSerializer
from .rbac import filter_patient_queryset, filter_highlights_queryset


class CareNoteView(APIView):
    """
    GET /api/patients/{patient_id}/care-note/
    returns: glance(highlights) + timeline(entries)
    """
    def get(self, request, patient_id: int):
        patient = get_object_or_404(Patient, id=patient_id)

        try:
            entries_qs = filter_patient_queryset(request.user, patient)
            hl_qs = filter_highlights_queryset(request.user, patient)
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        timeline = EntrySerializer(entries_qs, many=True).data
        highlights = HighlightSerializer(hl_qs, many=True).data

        glance = {
            "patient_display_name": patient.display_name,
            "highlights": highlights,
        }
        return Response({"patient_id": patient.id, "glance": glance, "timeline": timeline})

from rest_framework.permissions import IsAuthenticated
from .models import Entry
from .permissions import CanEditEntry
from .editing import get_latest_version, snapshot_and_update_entry, revert_entry_to_version
from .serializers import VersionSnapshotSerializer

class EntryEditView(APIView):
    permission_classes = [IsAuthenticated, CanEditEntry]

    def post(self, request, entry_id: int):
        entry = get_object_or_404(Entry, id=entry_id)

        # object-level permission
        self.check_object_permissions(request, entry)

        new_content = request.data.get("content", "")
        if not isinstance(new_content, str) or not new_content.strip():
            return Response({"detail": "content required"}, status=status.HTTP_400_BAD_REQUEST)

        # optimistic concurrency: If-Match: <version>
        expected = request.headers.get("If-Match")
        current = get_latest_version(entry)
        if expected is not None:
            try:
                expected_v = int(expected)
            except ValueError:
                return Response({"detail": "Invalid If-Match"}, status=status.HTTP_400_BAD_REQUEST)
            if expected_v != current:
                return Response(
                    {"detail": "Version conflict", "current_version": current},
                    status=status.HTTP_409_CONFLICT
                )

        new_ver = snapshot_and_update_entry(entry, new_content, request.user)
        return Response({"entry_id": entry.id, "new_version": new_ver})

class EntryVersionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, entry_id: int):
        entry = get_object_or_404(Entry, id=entry_id)
        qs = entry.versions.order_by("-version")
        return Response({"entry_id": entry.id, "versions": VersionSnapshotSerializer(qs, many=True).data})

class EntryRevertView(APIView):
    permission_classes = [IsAuthenticated, CanEditEntry]

    def post(self, request, entry_id: int, version: int):
        entry = get_object_or_404(Entry, id=entry_id)
        self.check_object_permissions(request, entry)

        try:
            new_ver = revert_entry_to_version(entry, version, request.user)
        except ValueError:
            return Response({"detail": "version not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"entry_id": entry.id, "new_version": new_ver, "reverted_to": version})

from rest_framework.permissions import IsAuthenticated
from .models import Highlight
from .serializers import HighlightSerializer
from .highlights import generate_rule_based_highlights

class GenerateHighlightsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, patient_id: int):
        if request.user.role == "patient":
            return Response({"detail": "patient cannot generate highlights"}, status=status.HTTP_403_FORBIDDEN)

        patient = get_object_or_404(Patient, id=patient_id)

        # clinic scope: non-admin cannot cross clinic
        if request.user.role != "admin" and request.user.clinic_id and request.user.clinic_id != patient.clinic_id:
            return Response({"detail": "Cross-clinic access denied"}, status=status.HTTP_403_FORBIDDEN)

        # for MVP: regenerate by clearing old suggested highlights
        Highlight.objects.filter(patient=patient).delete()

        hs = generate_rule_based_highlights(patient, request.user)
        return Response({"created": len(hs), "highlights": HighlightSerializer(hs, many=True).data})

from .models import Highlight, AuditLog

class HighlightStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, highlight_id: int):
        if request.user.role == "patient":
            return Response({"detail": "patient cannot change highlight status"}, status=status.HTTP_403_FORBIDDEN)

        h = get_object_or_404(Highlight, id=highlight_id)
        patient = h.patient

        if request.user.role != "admin" and request.user.clinic_id and request.user.clinic_id != patient.clinic_id:
            return Response({"detail": "Cross-clinic access denied"}, status=status.HTTP_403_FORBIDDEN)

        if request.user.role not in {"clinician", "admin"}:
            return Response({"detail": "Only clinician/admin can approve/reject"}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get("status")
        if new_status not in {"suggested", "accepted", "rejected"}:
            return Response({"detail": "status must be suggested/accepted/rejected"}, status=status.HTTP_400_BAD_REQUEST)

        old = h.status
        h.status = new_status
        h.save(update_fields=["status"])

        AuditLog.objects.create(
            patient=patient,
            actor=request.user,
            action="set_highlight_status",
            meta={"highlight_id": h.id, "from": old, "to": new_status},
        )

        return Response({"highlight_id": h.id, "status": h.status})
import uuid
from .models import Entry

class GenerateMockPatientSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, patient_id: int):
        if request.user.role == "patient":
            return Response({"detail": "patient cannot generate AI notes"}, status=status.HTTP_403_FORBIDDEN)

        patient = get_object_or_404(Patient, id=patient_id)
        if request.user.role != "admin" and request.user.clinic_id and request.user.clinic_id != patient.clinic_id:
            return Response({"detail": "Cross-clinic access denied"}, status=status.HTTP_403_FORBIDDEN)

        # 使用最近几条记录拼一个“像 AI 的”摘要
        Entry.objects.filter(patient=patient, type="ai_patient_session_summary").delete()
        recent = Entry.objects.filter(patient=patient).exclude(type="ai_patient_session_summary").order_by("-created_at")[:5]

        bullets = []
        for e in reversed(list(recent)):
            bullets.append(f"- ({e.type}) {e.content[:80]}")

        summary = (
            "Patient Summary (Mock AI)\n"
            "What happened:\n" + "\n".join(bullets) + "\n\n"
            "Next steps:\n- Monitor symptoms\n- Follow clinician advice\n"
        )

        prov = f"session:{uuid.uuid4().hex}"
        e = Entry.objects.create(
            patient=patient,
            author=None,
            author_role="system",
            type="ai_patient_session_summary",
            provenance_pointer=prov,
            content=summary,
        )
        AuditLog.objects.create(
            patient=patient,
            actor=request.user,
            action="generate_patient_summary_mock",
            meta={"entry_id": e.id},
        )
        return Response({"entry_id": e.id, "provenance_pointer": prov})
