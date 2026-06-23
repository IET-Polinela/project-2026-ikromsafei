from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Report
from .serializers import ReportSerializer

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Menampilkan semua data laporan di tabel teratas
        return Report.objects.all().order_by('-id')

    def perform_create(self, serializer):
        # Menghubungkan reporter ke user yang sedang login lewat token JWT
        serializer.save(reporter=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user = request.user

        # LOGIKA 1: Jika yang akses adalah Warga/Client, TOLAK (Gak boleh ngedit)
        if not user.is_staff and not user.is_superuser:
            return Response(
                {"detail": "Gagal! Warga/Client hanya bisa menambah laporan, tidak diizinkan mengubah data."},
                status=status.HTTP_403_FORBIDDEN
            )

        # LOGIKA 2: Jika Admin mau edit, tapi statusnya 'draft', TOLAK
        if instance.status.lower() == 'draft':
            return Response(
                {"detail": "Gagal! Admin tidak diizinkan mengubah laporan yang statusnya masih Draft."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Jika lolos validasi, Admin diizinkan mengubah data
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)