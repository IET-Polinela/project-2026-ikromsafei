from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from main_app.models import Report

# ─────────────────────────────────────────────────────────────────────────────
# PENJELASAN: get_user_model()
# ─────────────────────────────────────────────────────────────────────────────
# Django mendukung custom user model melalui setting AUTH_USER_MODEL.
# Pada proyek ini, user model kustom didefinisikan di usermanagement.User.
# Menggunakan get_user_model() memastikan kita selalu mereferensikan model
# user yang benar, bukan django.contrib.auth.models.User bawaan.
# ─────────────────────────────────────────────────────────────────────────────
User = get_user_model()

# =============================================================================
# MODUL 1: PENGUJIAN OTORISASI & MANAJEMEN SESI
# =============================================================================
# Fokus: Mekanisme autentikasi JWT (JSON Web Token), penolakan kredensial
# salah, dan pembatasan hak akses berbasis peran (role-based access control).
#
# Catatan:
# - AUTH-01 s/d AUTH-03 diuji menggunakan Script Python (APITestCase).
# - AUTH-04 s/d AUTH-06 diuji menggunakan Script Playwright (E2E) karena
#   membutuhkan simulasi browser nyata dengan localStorage dan hash routing.
#   Lihat file: tests/e2e/citizen_portal.spec.js
# =============================================================================

class AuthenticationTests(APITestCase):
    """
    Kelas pengujian untuk modul Otorisasi & Manajemen Sesi.

    Menguji mekanisme login JWT dan pembatasan akses endpoint berdasarkan
    peran pengguna (warga biasa vs admin).
    """

    def setUp(self):
        """
        Persiapan data uji yang dijalankan SEBELUM setiap method test.

        PENJELASAN setUp():
        Method ini membuat objek-objek yang dibutuhkan oleh test. Django akan
        jalankan setUp() sebelum SETIAP test method secara otomatis, lalu
        melakukan rollback database setelahnya. Ini memastikan setiap test
        berjalan secara independen tanpa saling mempengaruhi.
        """
        # Buat user warga biasa (is_admin=False secara default dari model)
        # Warga ini mewakili pengguna SPA Citizen Portal
        self.warga = User.objects.create_user(
            username='warga_test',
            password='Password123!',
            is_admin=False,  # Bukan admin — hanya bisa akses API Citizen
        )

        # Buat user admin (is_admin=True)
        # Admin ini mewakili petugas yang mengakses Portal Admin (Django monolitik)
        self.admin = User.objects.create_user(
            username='admin_test',
            password='AdminPass123!',
            is_admin=True,
            is_staff=True,  # Diperlukan agar bisa akses @staff_member_required views
        )

    # ─────────────────────────────────────────────────────────────────────────
    # AUTH-01: Login Warga dengan Kredensial Valid
    # ─────────────────────────────────────────────────────────────────────────
    def test_AUTH_01_login_warga_dengan_kredensial_valid(self):
        """
        [AUTH-01] Login Warga dengan kredensial valid pada endpoint token.

        SKENARIO:
            Pengguna mengirim POST request ke endpoint /api/token/ dengan
            username dan password yang benar.

        HASIL YANG DIHARAPKAN:
            Sistem mengembalikan `access_token` dan `refresh_token` dengan
            status HTTP 200 OK.

        PENJELASAN TEKNIS:
            Endpoint /api/token/ disediakan oleh library `djangorestframework-
            simplejwt`. Ketika kredensial valid, server mengeluarkan sepasang
            token JWT:
            - access: Token utama yang dikirim di header Authorization
            - refresh: Token cadangan untuk memperbarui access jika expired
        """
        url = reverse('token_obtain_pair')
        payload = {
            'username': 'warga_test',
            'password': 'Password123!',
        }

        response = self.client.post(url, payload, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "Login dengan kredensial valid seharusnya mengembalikan HTTP 200"
        )
        self.assertIn(
            'access',
            response.data,
            "Respons login harus mengandung field 'access' (JWT Access Token)"
        )
        self.assertIn(
            'refresh',
            response.data,
            "Respons login harus mengandung field 'refresh' (JWT Refresh Token)"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # AUTH-02: Login Warga dengan Password Salah
    # ─────────────────────────────────────────────────────────────────────────
    def test_AUTH_02_login_warga_dengan_password_salah(self):
        """
        [AUTH-02] Login Warga dengan kata sandi (password) salah.

        SKENARIO:
            Pengguna mengirim POST request ke endpoint /api/token/ dengan
            username yang benar namun password yang salah.

        HASIL YANG DIHARAPKAN:
            Sistem menolak akses dan mengembalikan status HTTP 401 Unauthorized.

        PENJELASAN TEKNIS:
            SimpleJWT melakukan autentikasi menggunakan backend autentikasi
            Django. Jika password tidak cocok, Django menolak autentikasi dan
            SimpleJWT mengembalikan respons 401 tanpa mengeluarkan token.
        """
        url = reverse('token_obtain_pair')
        payload = {
            'username': 'warga_test',
            'password': 'passwordSALAH',  # Password ini tidak cocok!
        }

        response = self.client.post(url, payload, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Login dengan password salah seharusnya mengembalikan HTTP 401"
        )
        self.assertNotIn(
            'access',
            response.data,
            "Tidak boleh ada token yang dikeluarkan untuk kredensial invalid"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # AUTH-03: Warga Biasa Mengakses Endpoint/Halaman Admin
    # ─────────────────────────────────────────────────────────────────────────
    def test_AUTH_03_warga_tidak_bisa_akses_halaman_admin(self):
        """
        [AUTH-03] Pengguna berstatus Warga biasa (is_admin=False) mencoba
        mengakses URL endpoint/halaman portal Admin.

        SKENARIO:
            Warga biasa yang sudah login mencoba mengakses halaman dashboard
            yang hanya dapat diakses oleh admin

        HASIL YANG DIHARAPKAN:
            Sistem menolak permintaan. Karena warga biasa tidak memiliki hak akses, 
            respons berupa HTTP 302.

        PENJELASAN TEKNIS:
            Portal admin menggunakan Django session-based auth, bukan JWT.
            Cek apakah user memiliki is_staff=True. Jika tidak, Django 
            memberikan respons HTTP 302.
        """
        # ARRANGE: Lakukan login ke session client menggunakan akun warga biasa (non-staff)
        self.client.login(username='warga_test', password='Password123!')
        
        # ACT: Mencoba melakukan GET request paksa ke rute dashboard admin
        response = self.client.get(reverse('admin_dashboard'))
        
        # ASSERT: Ubah dari 302 menjadi 403 mengikuti sistem aslimu
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Warga biasa yang mencoba masuk ke dashboard admin harus diblok (HTTP 403)"
        )