from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from rest_framework.routers import DefaultRouter
from main_app.api_views import ReportViewSet
from main_app.models import Report
from usermanagement.api_views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# 1. Konfigurasi Router untuk REST API Kelompokmu
router = DefaultRouter()
router.register(r'report', ReportViewSet, basename='report')

User = get_user_model()

# ========================================================
# FUNGSI VIEW UTAMA (LOGIKA BACKEND)
# ========================================================

# View Utama Landing Page (Menampilkan Tabel Keluhan)
def backend_landing_page(request):
    reports_data = Report.objects.all().order_by('-id')
    return render(request, 'backend_home.html', {'reports': reports_data})

# View Proses Login Depan
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
    return redirect('backend_home_root')

# View Proses Otomatis Registrasi Warga Baru (Masyarakat)
def register_frontend_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        
        # Validasi jika username sudah dipakai di database kustom
        if User.objects.filter(username=u).exists():
            messages.error(request, 'Username tersebut sudah terdaftar! Gunakan nama lain.')
            return redirect('backend_home_root')
            
        try:
            # Membuat user baru secara aman di database kustom
            new_warga = User.objects.create_user(username=u, email=e, password=p)
            new_warga.is_citizen = True  # <--- Otomatis terset sebagai Warga/Citizen
            new_warga.is_admin = False   # <--- Menjamin akun baru bukan Admin aplikasi
            new_warga.is_staff = False
            new_warga.save()
            
            messages.success(request, 'Akun Warga berhasil dibuat! Silakan login.')
            return redirect('backend_home_root')
        except Exception as error:
            messages.error(request, f'Gagal mendaftar: {str(error)}')
            return redirect('backend_home_root')
            
    return redirect('backend_home_root')

# View Proses Logout
def logout_frontend_view(request):
    logout(request)
    messages.info(request, 'Sesi Anda telah berakhir.')
    return redirect('backend_home_root')


# ========================================================
# URL PATTERNS (RUTE JALUR APLIKASI KOTA IET)
# ========================================================
urlpatterns = [
    # Jalur Tampilan Depan & Otentikasi yang Sinkron dengan HTML Modal
    path('', backend_landing_page, name='backend_home_root'), 
    path('login-frontend/', login_frontend_view, name='login_frontend'),
    path('register-frontend/', register_frontend_view, name='register_frontend'),
    path('logout-frontend/', logout_frontend_view, name='logout_frontend'),
    
    # Jalur Admin Panel Django Bawaan Server
    path('admin/', admin.site.urls),
    
    # Jalur API (Endpoint untuk kebutuhan djangorestframework)
    path('api/', include(router.urls)),
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]