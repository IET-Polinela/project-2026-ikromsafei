from rest_framework import permissions

class IsOwnerAndDraftOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Operasi baca (GET) diizinkan untuk semua user terautentikasi (Lab 10)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Modifikasi (PUT/PATCH/DELETE) wajib milik pembuat laporan dan statusnya masih DRAFT (Lab 10)
        return obj.reporter == request.user and obj.status == 'DRAFT'