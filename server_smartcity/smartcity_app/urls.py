from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from rest_framework.routers import DefaultRouter
from main_app.api_views import ReportViewSet
from main_app.models import Report
from usermanagement.api_views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'report', ReportViewSet, basename='report')

User = get_user_model()

# ========================================================
# VIEWS FRONTEND - DENGAN PENGAMAN MULTIVALUEDICTKEYERROR
# ========================================================

def backend_landing_page(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            # Admin melihat semua data
            reports_data = Report.objects.all().order_by('-id')
            total_laporan = Report.objects.count()
            jumlah_reported = Report.objects.filter(status__iexact='REPORTED').count()
            jumlah_in_progress = Report.objects.filter(status__iexact='IN_PROGRESS').count()
            jumlah_verified = Report.objects.filter(status__iexact='VERIFIED').count()
            jumlah_resolved = Report.objects.filter(status__iexact='RESOLVED').count()
            jumlah_draft = Report.objects.filter(status__iexact='draft').count()
        else:
            # Warga/Client melihat miliknya sendiri
            reports_data = Report.objects.filter(user=request.user).order_by('-id')
            total_laporan = Report.objects.filter(user=request.user).count()
            jumlah_reported = Report.objects.filter(user=request.user, status__iexact='REPORTED').count()
            jumlah_in_progress = Report.objects.filter(user=request.user, status__iexact='IN_PROGRESS').count()
            jumlah_verified = Report.objects.filter(user=request.user, status__iexact='VERIFIED').count()
            jumlah_resolved = Report.objects.filter(user=request.user, status__iexact='RESOLVED').count()
            jumlah_draft = Report.objects.filter(user=request.user, status__iexact='draft').count()
    else:
        reports_data = []
        total_laporan = jumlah_reported = jumlah_in_progress = jumlah_verified = jumlah_resolved = jumlah_draft = 0

    konteks = {
        'reports': reports_data,
        'total_laporan': total_laporan,
        'jumlah_reported': jumlah_reported,
        'jumlah_in_progress': jumlah_in_progress,
        'jumlah_verified': jumlah_verified,
        'jumlah_resolved': jumlah_resolved,
        'jumlah_draft': jumlah_draft,
    }
    return render(request, 'backend_home.html', konteks)

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
        
        # FIX: Gunakan .get() dengan fallback 'REPORTED' agar anti-error walaupun key status kosong
        s = request.POST.get('status', 'REPORTED')
        if not s:
            s = 'REPORTED'
            
        try:
            Report.objects.create(title=t, location=l, status=s, user=request.user)
            messages.success(request, 'Laporan aduan baru berhasil disimpan ke sistem!')
        except Exception as e:
            messages.error(request, f'Gagal menyimpan laporan: {str(e)}')
    return redirect('backend_home_root')

def ubah_laporan_frontend(request, pk):
    if request.method == 'POST' and request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            laporan = get_object_or_404(Report, pk=pk)
            laporan.status = request.POST.get('status', 'REPORTED')
            laporan.save()
            messages.success(request, f'Status laporan ID #{pk} berhasil diperbarui!')
        else:
            messages.error(request, 'Akses ditolak! Anda bukan admin.')
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
    
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]