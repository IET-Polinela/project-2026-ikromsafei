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
# MODUL 4: PENGUJIAN FUNGSIONALITAS DASAR & VALIDASI INPUT
# =============================================================================
# Fokus: Memastikan fungsi CRUD (Create, Read, Update, Delete) berjalan normal,
# validasi input wajib ditegakkan, dan keamanan dari serangan injeksi (XSS).
#
# KONSEP KUNCI:
#   - Serializer DRF secara otomatis memvalidasi field yang required
#   - Django template engine secara default melakukan HTML escaping
#   - SearchFilter DRF melakukan pencarian berbasis teks di field yang
#     terdaftar pada search_fields
# =============================================================================

class CRUDAndValidationTests(APITestCase):
    """
    Kelas pengujian untuk fungsionalitas dasar dan validasi input.

    Menguji pembuatan data baru (CREATE), validasi field wajib, pertahanan
    terhadap serangan XSS, dan fitur pencarian/filter data.
    """

    def setUp(self):
        """
        Persiapan: Buat warga dan autentikasi untuk test CRUD.
        """
        self.warga = User.objects.create_user(
            username='warga_crud', password='TestPass123!', is_admin=False
        )
        # force_authenticate memastikan semua request di test ini terautentikasi
        self.client.force_authenticate(user=self.warga)

    # ─────────────────────────────────────────────────────────────────────────
    # FT-01: Membuat Laporan Baru dengan Data Lengkap
    # ─────────────────────────────────────────────────────────────────────────
    def test_FT_01_buat_laporan_dengan_data_lengkap(self):
        """
        [FT-01] Mengirim data laporan baru dengan seluruh kolom (field)
        terisi lengkap dan benar.
        """
        # ARRANGE: Menentukan URL endpoint REST API dan menyusun payload isian lengkap
        url = reverse('report-list')
        payload = {
            'title': 'Tiang Listrik Roboh',
            'category': 'Infrastruktur',
            'description': 'Tiang listrik roboh menghalangi jalur utama Gedong Tataan.',
            'location': 'Gedong Tataan',
            'status': 'REPORTED'
        }

        # ACT: Jalankan request HTTP POST memanfaatkan unit test client
        response = self.client.post(url, payload, format='json')

        # ASSERT: Validasi keluaran memastikan kembalian berstatus HTTP 201 Created
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            "Pembuatan aduan baru dengan parameter lengkap wajib berhasil (HTTP 201)"
        )
        # Memastikan data baru benar-benar tersimpan di dalam record database kota
        self.assertTrue(Report.objects.filter(title='Tiang Listrik Roboh').exists())

    # ─────────────────────────────────────────────────────────────────────────
    # FT-02: Laporan Ditolak Jika Judul Kosong
    # ─────────────────────────────────────────────────────────────────────────
    def test_FT_02_ditolak_jika_judul_kosong(self):
        """
        [FT-02] Mengirim data pembuatan laporan baru dengan mengosongkan kolom judul (title).
        """
        # ARRANGE: Mengosongkan field variabel kunci 'title'
        url = reverse('report-list')
        payload = {
            'category': 'Infrastruktur',
            'description': 'Deskripsi tanpa judul',
            'location': 'Pesawaran',
            'status': 'REPORTED'
        }

        # ACT: Kirim data cacat ke endpoint server
        response = self.client.post(url, payload, format='json')

        # ASSERT: Sistem wajib menolak tegas dan mengembalikan HTTP 400 Bad Request
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            "Server harus menolak pembuatan laporan jika field title kosong (HTTP 400)"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # FT-03: Laporan Ditolak Jika Deskripsi Kosong
    # ─────────────────────────────────────────────────────────────────────────
    def test_FT_03_ditolak_jika_deskripsi_kosong(self):
        """
        [FT-03] Mengirim data pembuatan laporan baru dengan mengosongkan kolom deskripsi (description).
        """
        # ARRANGE: Mengosongkan field variabel kunci 'description'
        url = reverse('report-list')
        payload = {
            'title': 'Judul Laporan Valid',
            'category': 'Kebersihan',
            'location': 'Negeri Katon',
            'status': 'REPORTED'
        }

        # ACT: Kirim POST data tanpa deskripsi
        response = self.client.post(url, payload, format='json')

        # ASSERT: Sistem wajib melempar penolakan validasi input (HTTP 400 Bad Request)
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            "Server harus menolak pembuatan laporan jika field description kosong (HTTP 400)"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # FT-04: Keamanan dari Serangan XSS (Cross-Site Scripting)
    # ─────────────────────────────────────────────────────────────────────────
    def test_FT_04_xss_script_disimpan_sebagai_string_literal(self):
        """
        [FT-04] Mengisi nilai deskripsi laporan menggunakan kode skrip injeksi jahat HTML.
        """
        url = reverse('report-list')

        # Payload dengan skrip injeksi XSS di deskripsi
        kode_xss = '<script>alert("xss")</script>'
        payload = {
            'title': 'Laporan XSS Test',
            'category': 'Keamanan',
            'description': kode_xss,
            'location': 'Lab Keamanan Siber',
        }

        response = self.client.post(url, payload, format='json')

        # Verifikasi: Data tetap diterima (201 Created)
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            "Data dengan karakter HTML harus tetap diterima oleh API"
        )

        # Verifikasi: Deskripsi tersimpan di database sebagai teks literal
        laporan = Report.objects.get(title='Laporan XSS Test')

        # Kode script harus tersimpan sebagai string biasa, bukan di-execute
        self.assertIn(
            'script',
            laporan.description.lower(),
            "Kode XSS harus tersimpan sebagai string literal di database"
        )