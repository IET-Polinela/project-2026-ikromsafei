from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse # Ditambahkan untuk suplai data Chart.js
from rest_framework.routers import DefaultRouter
from main_app.api_views import ReportViewSet
from main_app.models import Report
from usermanagement.api_views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import pustaka dokumentasi OpenAPI Lab 14
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django_scalar.views import scalar_viewer

router = DefaultRouter()
router.register(r'report', ReportViewSet, basename='report')

User = get_user_model()

# ========================================================
# VIEWS FRONTEND - SINKRONISASI ROLE & FILTER DATA
# ========================================================

def backend_landing_page(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            # Admin melihat semua data keluhan (Kecuali status 'draft')
            reports_data = Report.objects.exclude(status__iexact='draft').order_by('-id')
            total_laporan = Report.objects.exclude(status__iexact='draft').count()
            
            # Mengambil 5 data laporan terbaru khusus untuk tabel info bawah dashboard
            latest_reported = Report.objects.filter(status__iexact='REPORTED').order_by('-id')[:5]
            latest_resolved = Report.objects.filter(status__iexact='RESOLVED').order_by('-id')[:5]
            
            jumlah_reported = Report.objects.filter(status__iexact='REPORTED').count()
            jumlah_in_progress = Report.objects.filter(status__iexact='IN_PROGRESS').count()
            jumlah_verified = Report.objects.filter(status__iexact='VERIFIED').count()
            jumlah_resolved = Report.objects.filter(status__iexact='RESOLVED').count()
            jumlah_draft = 0
        else:
            # FIX: Warga melihat draft miliknya sendiri ATAU semua laporan publik yang BUKAN draft (~Q)
            reports_data = Report.objects.filter(
                Q(status__iexact='draft', reporter=request.user) | 
                ~Q(status__iexact='draft')
            ).order_by('-id')
            
            total_laporan = reports_data.count()
            latest_reported = Report.objects.filter(status__iexact='REPORTED').order_by('-id')[:5]
            latest_resolved = Report.objects.filter(status__iexact='RESOLVED').order_by('-id')[:5]
            
            jumlah_reported = Report.objects.filter(status__iexact='REPORTED').count()
            jumlah_in_progress = Report.objects.filter(status__iexact='IN_PROGRESS').count()
            jumlah_verified = Report.objects.filter(status__iexact='VERIFIED').count()
            jumlah_resolved = Report.objects.filter(status__iexact='RESOLVED').count()
            jumlah_draft = Report.objects.filter(reporter=request.user, status__iexact='draft').count()
    else:
        reports_data = []
        latest_reported = []
        latest_resolved = []
        total_laporan = jumlah_reported = jumlah_in_progress = jumlah_verified = jumlah_resolved = jumlah_draft = 0

    konteks = {
        'reports': reports_data,
        'latest_reported': latest_reported,
        'latest_resolved': latest_resolved,
        'total_laporan': total_laporan,
        'jumlah_reported': jumlah_reported,
        'jumlah_in_progress': jumlah_in_progress,
        'jumlah_verified': jumlah_verified,
        'jumlah_resolved': jumlah_resolved,
        'jumlah_draft': jumlah_draft,
    }
    return render(request, 'backend_home.html', konteks)

# API Endpoint khusus penyuplai data angka Chart.js ke template HTML
def dashboard_api_data(request):
    draft_count = Report.objects.filter(status__iexact='draft').count()
    reported_count = Report.objects.filter(status__iexact='reported').count()
    verified_count = Report.objects.filter(status__iexact='verified').count()
    resolved_count = Report.objects.filter(status__iexact='resolved').count()
    
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

def login_frontend_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            messages.success(request, f'Selamat datang kembali, {u}!')
            return redirect('backend_home_root')
        else:
            messages.error(request, 'Gagal masuk! Username atau Password salah.')
    return redirect('backend_home_root')

def register_frontend_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        if User.objects.filter(username=u).exists():
            messages.error(request, 'Username sudah terdaftar!')
            return redirect('backend_home_root')
        try:
            new_warga = User.objects.create_user(username=u, email=e, password=p)
            new_warga.is_citizen = True
            new_warga.save()
            messages.success(request, 'Akun Warga berhasil dibuat! Silakan login.')
        except Exception as error:
            messages.error(request, f'Gagal: {str(error)}')
    return redirect('backend_home_root')

def logout_frontend_view(request):
    logout(request)
    messages.info(request, 'Sesi Anda telah berakhir.')
    return redirect('backend_home_root')

def tambah_laporan_frontend(request):
    if request.method == 'POST' and request.user.is_authenticated:
        t = request.POST.get('title')
        l = request.POST.get('location')
        s = request.POST.get('status', 'REPORTED')
        
        if not s:
            s = 'REPORTED'
            
        try:
            Report.objects.create(title=t, location=l, status=s, reporter=request.user)
            messages.success(request, 'Laporan aduan baru berhasil disimpan ke sistem!')
        except Exception as e:
            messages.error(request, f'Gagal menyimpan laporan: {str(e)}')
    return redirect('backend_home_root')

def ubah_laporan_frontend(request, pk):
    if request.method == 'POST' and request.user.is_authenticated:
        laporan = get_object_or_404(Report, pk=pk)
        
        if request.user.is_staff or request.user.is_superuser:
            laporan.status = request.POST.get('status', 'REPORTED')
            laporan.save()
            messages.success(request, f'Status laporan ID #{pk} berhasil diperbarui!')
            
        elif laporan.reporter == request.user and laporan.status.lower() == 'draft':
            laporan.title = request.POST.get('title', laporan.title)
            laporan.location = request.POST.get('location', laporan.location)
            laporan.status = request.POST.get('status', 'draft')
            laporan.save()
            messages.success(request, f'Draft aduan ID #{pk} berhasil diperbarui!')
        else:
            messages.error(request, 'Akses ditolak!')
            
    return redirect('backend_home_root')

def hapus_laporan_frontend(request, pk):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        laporan = get_object_or_404(Report, pk=pk)
        laporan.delete()
        messages.success(request, f'Laporan ID #{pk} berhasil dihapus!')
    else:
        messages.error(request, 'Akses ditolak!')
    return redirect('backend_home_root')

# ========================================================
# URL PATTERNS
# ========================================================
urlpatterns = [
    path('', backend_landing_page, name='backend_home_root'), 
    path('login-frontend/', login_frontend_view, name='login_frontend'),
    path('register-frontend/', register_frontend_view, name='register_frontend'),
    path('logout-frontend/', logout_frontend_view, name='logout_frontend'),
    
    path('tambah-laporan/', tambah_laporan_frontend, name='tambah_laporan_frontend'),
    path('ubah-laporan/<int:pk>/', ubah_laporan_frontend, name='ubah_laporan_frontend'),
    path('hapus-laporan/<int:pk>/', hapus_laporan_frontend, name='hapus_laporan_frontend'),
    
    # Endpoint API khusus penyuplai data Chart.js
    path('dashboard/api/data/', dashboard_api_data, name='dashboard_api'),
    
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # OpenAPI-based Documentation Routing
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/scalar/', scalar_viewer, name='scalar-ui'),
]