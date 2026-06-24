from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Report
from .serializers import ReportSerializer

@extend_schema(exclude=True)
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

# ─────────────────────────────────────────────────────────────────────────────
# TAMBAHAN UNTUK DASHBOARD ANALITIK MONOLITIK (WARNA TEMATIK PESAWARAN)
# ─────────────────────────────────────────────────────────────────────────────
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    """View untuk merender halaman HTML Dashboard Analitik"""
    # Mengamankan halaman agar hanya bisa dibuka oleh Admin/Staff
    if not request.user.is_staff and not request.user.is_superuser:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Anda tidak memiliki izin untuk mengakses halaman dashboard ini.")
        
    # Mengambil 5 data laporan terbaru berdasarkan status untuk tabel bawah
    latest_reported = Report.objects.filter(status='REPORTED').order_by('-id')[:5]
    latest_resolved = Report.objects.filter(status='RESOLVED').order_by('-id')[:5]
    
    context = {
        'latest_reported': latest_reported,
        'latest_resolved': latest_resolved,
    }
    return render(request, 'main_app/dashboard.html', context)


def dashboard_api_data(request):
    """Endpoint API pendukung untuk menyuplai data angka ke Chart.js"""
    # 1. Hitung total data real-time berdasarkan Status
    draft_count = Report.objects.filter(status__iexact='draft').count()
    reported_count = Report.objects.filter(status__iexact='reported').count()
    verified_count = Report.objects.filter(status__iexact='verified').count()
    resolved_count = Report.objects.filter(status__iexact='resolved').count()
    
    # 2. Hitung total data real-time berdasarkan Kategori
    kategori_data = {
        'Fasilitas': Report.objects.filter(category__icontains='fasilitas').count(),
        'Infrastruktur': Report.objects.filter(category__icontains='infrastruktur').count(),
        'Kebersihan': Report.objects.filter(category__icontains='kebersihan').count(),
        'Keamanan': Report.objects.filter(category__icontains='keamanan').count(),
        'Lainnya': Report.objects.filter(category__icontains='lainnya').count(),
    }
    
    return JsonResponse({
        'status': {
            'draft': draft_count,
            'reported': reported_count,
            'verified': verified_count,
            'resolved': resolved_count,
        },
        'kategori': kategori_data
    })