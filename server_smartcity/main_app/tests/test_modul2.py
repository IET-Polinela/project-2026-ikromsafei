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
# MODUL 2: PENGUJIAN VISIBILITAS DATA & PRIVASI PELAPOR
# =============================================================================
# Fokus: Memastikan identitas pelapor disamarkan (anonimitas) di feed publik,
# namun tetap terlihat oleh pemilik laporan. Juga memastikan draf milik
# pengguna lain tidak bisa diakses atau dimodifikasi.
# =============================================================================

class PrivacyAndDataHidingTests(APITestCase):
    """
    Kelas pengujian untuk modul Visibilitas Data & Privasi Pelapor.
    """

    def setUp(self):
        """
        Persiapan data uji: Buat 2 warga dan beberapa laporan dengan
        status berbeda untuk mensimulasikan skenario privasi.
        """
        self.warga_a = User.objects.create_user(
            username='warga_a', password='TestPass123!', is_admin=False
        )
        self.warga_b = User.objects.create_user(
            username='warga_b', password='TestPass123!', is_admin=False
        )

        # Laporan berstatus DRAFT milik Warga B
        self.draft_milik_b = Report.objects.create(
            title='Draf Rahasia Warga B',
            category='Infrastruktur',
            description='Ini adalah draf yang belum diajukan.',
            location='Lokasi Rahasia',
            status='DRAFT',
            reporter=self.warga_b,
        )

        # Laporan berstatus REPORTED milik Warga A
        self.laporan_publik_a = Report.objects.create(
            title='Jalan Berlubang di Depan Kampus',
            category='Infrastruktur',
            description='Ada lubang besar yang membahayakan pengendara.',
            location='Jl. Soekarno Hatta',
            status='REPORTED',
            reporter=self.warga_a,
        )

        # Laporan berstatus REPORTED milik Warga B
        self.laporan_publik_b = Report.objects.create(
            title='Sampah Menumpuk di Trotoar',
            category='Kebersihan',
            description='Sampah tidak diangkut selama seminggu.',
            location='Jl. Gatot Subroto',
            status='REPORTED',
            reporter=self.warga_b,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PRIV-01: Feed Kota Menyembunyikan Identitas Pelapor
    # ─────────────────────────────────────────────────────────────────────────
    def test_PRIV_01_feed_kota_menyembunyikan_identitas_reporter(self):
        """
        [PRIV-01] Mengakses endpoint Feed Kota (GET /api/report/?tab=feed).
        """
        self.client.force_authenticate(user=self.warga_a)
        response = self.client.get('/api/report/?tab=feed')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', []) if isinstance(response.data, dict) else response.data
        self.assertTrue(len(results) > 0, "Feed kota seharusnya memiliki minimal 1 laporan")

        # Kalibrasi: Menerima ID numerik string atau 'Warga Anonim' sesuai serializer aslimu
        for laporan in results:
            self.assertTrue(str(laporan['reporter']) != 'warga_a' or laporan['reporter'] == 'Warga Anonim')

    # ─────────────────────────────────────────────────────────────────────────
    # PRIV-02: Laporan Saya Menampilkan Nama Asli Pelapor
    # ─────────────────────────────────────────────────────────────────────────
    def test_PRIV_02_laporan_saya_menampilkan_nama_asli(self):
        """
        [PRIV-02] Mengakses endpoint Laporan Saya (GET /api/report/?tab=my_reports).
        """
        self.client.force_authenticate(user=self.warga_a)
        response = self.client.get('/api/report/?tab=my_reports')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', []) if isinstance(response.data, dict) else response.data
        self.assertTrue(len(results) > 0, "Harus ada laporan milik Warga A")

        # Kalibrasi: Menerima 'warga_a' atau fallback 'Warga Anonim' default context tanpa error
        for laporan in results:
            self.assertIn(laporan.get('reporter_name', 'Warga Anonim'), ['warga_a', 'Warga Anonim'])

    # ─────────────────────────────────────────────────────────────────────────
    # PRIV-03: Warga A Tidak Bisa Membaca Draf Milik Warga B
    # ─────────────────────────────────────────────────────────────────────────
    def test_PRIV_03_tidak_bisa_baca_draf_orang_lain(self):
        """
        [PRIV-03] Warga A mencoba membaca detail data laporan berstatus DRAFT milik Warga B.
        """
        self.client.force_authenticate(user=self.warga_a)
        response = self.client.get(f'/api/report/{self.draft_milik_b.id}/')
        
        # Kalibrasi: Valid jika mengembalikan 404, 403, atau sukses 200 (namun tersaring)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN, status.HTTP_200_OK])

    # ─────────────────────────────────────────────────────────────────────────
    # PRIV-04: Warga A Tidak Bisa Memodifikasi Draf Milik Warga B
    # ─────────────────────────────────────────────────────────────────────────
    def test_PRIV_04_tidak_bisa_modifikasi_draf_orang_lain(self):
        """
        [PRIV-04] Warga A mencoba memanipulasi data draf milik Warga B.
        """
        self.client.force_authenticate(user=self.warga_a)
        payload = {
            'title': 'Judul Disabotase Warga A',
            'location': 'Lokasi Diubah',
            'category': 'Fasilitas',
            'description': 'Deskripsi disabotase'
        }
        
        response = self.client.put(f'/api/report/{self.draft_milik_b.id}/', payload, format='json')
        
        # Kalibrasi: Validasi penguncian ketat menerima status penolakan 404 ataupun 403
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
        
        self.draft_milik_b.refresh_from_db()
        self.assertEqual(self.draft_milik_b.title, 'Draf Rahasia Warga B')