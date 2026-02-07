from django.db import transaction
from django.utils import timezone
from .models import Entry, VersionSnapshot, AuditLog

def get_latest_version(entry: Entry) -> int:
    last = entry.versions.order_by("-version").first()
    return last.version if last else 0

@transaction.atomic
def snapshot_and_update_entry(entry: Entry, new_content: str, actor):
    # create snapshot before change
    cur_ver = get_latest_version(entry)
    VersionSnapshot.objects.create(
        entry=entry,
        version=cur_ver + 1,
        content=new_content,
        changed_by=actor,
    )
    entry.content = new_content
    entry.updated_at = timezone.now()
    entry.save(update_fields=["content", "updated_at"])

    AuditLog.objects.create(
        patient=entry.patient,
        actor=actor,
        action="edit_entry",
        meta={"entry_id": entry.id, "new_version": cur_ver + 1},
    )
    return cur_ver + 1

@transaction.atomic
def revert_entry_to_version(entry: Entry, target_version: int, actor):
    snap = entry.versions.filter(version=target_version).first()
    if not snap:
        raise ValueError("version_not_found")

    # create a new snapshot that records the revert result as latest version
    cur_ver = get_latest_version(entry)
    VersionSnapshot.objects.create(
        entry=entry,
        version=cur_ver + 1,
        content=snap.content,
        changed_by=actor,
    )
    entry.content = snap.content
    entry.updated_at = timezone.now()
    entry.save(update_fields=["content", "updated_at"])

    AuditLog.objects.create(
        patient=entry.patient,
        actor=actor,
        action="revert_entry",
        meta={"entry_id": entry.id, "reverted_to": target_version, "new_version": cur_ver + 1},
    )
    return cur_ver + 1
