from rest_framework.permissions import BasePermission

class CanEditEntry(BasePermission):
    def has_object_permission(self, request, view, obj):
        u = request.user
        if u.role == "admin":
            return True
        if u.role == "staff":
            return obj.author_role == "staff" and obj.type == "staff_note"
        if u.role == "clinician":
            return obj.author_role == "clinician" and obj.type == "clinician_note"
        return False
