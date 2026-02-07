from rest_framework import serializers
from .models import Patient, Entry, Highlight


class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = [
            "id", "patient", "author", "author_role", "type",
            "created_at", "updated_at", "provenance_pointer", "content"
        ]


class HighlightSerializer(serializers.ModelSerializer):
    entry_id = serializers.IntegerField(source="entry.id", read_only=True)

    class Meta:
        model = Highlight
        fields = [
            "id", "text", "risk_reason", "status",   # <- 必须有 status
            "entry_id", "span_start", "span_end", "created_at"
        ]


class CareNoteSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    glance = serializers.DictField()
    timeline = serializers.ListField()

from .models import VersionSnapshot

class VersionSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionSnapshot
        fields = ["version", "content", "created_at", "changed_by"]
