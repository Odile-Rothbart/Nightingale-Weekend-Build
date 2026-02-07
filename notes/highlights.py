from typing import List
from .models import Patient, Entry, Highlight, AuditLog

RISK_KEYWORDS = [
    ("allergy", "Possible allergy mentioned"),
    ("chest pain", "Potential cardiac symptom"),
    ("shortness of breath", "Respiratory risk signal"),
    ("bleeding", "Bleeding risk signal"),
    ("suicidal", "Self-harm risk signal"),
]

def generate_rule_based_highlights(patient: Patient, actor) -> List[Highlight]:
    entries = (
    Entry.objects
    .filter(patient=patient)
    .exclude(type__startswith="ai_")   # 关键：排除 AI entries
    .order_by("-created_at")[:20]
)

    created = []
    MAX = 1

    for e in entries:
        if len(created) >= MAX:
            break
        text_lower = (e.content or "").lower()
        for kw, reason in RISK_KEYWORDS:
            if kw in text_lower:
                h = Highlight.objects.create(
                    patient=patient,
                    created_by=actor,
                    text=f"{kw}: {e.content[:120]}",
                    risk_reason=reason,
                    entry=e,
                    span_start=0,
                    span_end=min(len(e.content), 120),
                    status="suggested",
                )
                created.append(h)
                break

    AuditLog.objects.create(
        patient=patient,
        actor=actor,
        action="generate_highlights_rule",
        meta={"created": len(created)},
    )
    return created

    AuditLog.objects.create(
        patient=patient,
        actor=actor,
        action="generate_highlights",
        meta={"created": len(created)},
    )
    return created
