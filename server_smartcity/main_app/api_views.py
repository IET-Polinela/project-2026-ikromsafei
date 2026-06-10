from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Report
from .serializers import ReportSerializer # Sesuaikan nama serializer kelompokmu

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Mengembalikan semua data laporan untuk ditampilkan di tabel
        return Report.objects.all().order_by('-id')

    def perform_create(self, serializer):
        # Saat Warga/Client menambah laporan, otomatis simpan siapa pembuatnya
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user = request.user

        # -----------------------------------------------------------
        # LOGIKA 1: JIKA YANG AKSES ADALAH CLIENT (WARGA BUKAN ADMIN)
        # -----------------------------------------------------------
        if not user.is_staff and not user.is_superuser:
            return Response(
                {"detail": "Gagal! Warga/Client hanya bisa menambah laporan, tidak diizinkan mengubah data."},
                status=status.HTTP_403_FORBIDDEN
            )

        # -----------------------------------------------------------
        # LOGIKA 2: JIKA ADMIN INGIN MENGUBAH LAPORAN YANG MASIH DRAFT
        # -----------------------------------------------------------
        # Pastikan field status di model Report kelompokmu namanya 'status' 
        # dan nilai string untuk draf adalah 'draft' (silakan sesuaikan)
        if instance.status.lower() == 'draft':
            return Response(
                {"detail": "Gagal! Admin tidak diizinkan mengubah laporan yang statusnya masih Draft."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Jika lolos validasi di atas, izinkan Admin mengubah data
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)