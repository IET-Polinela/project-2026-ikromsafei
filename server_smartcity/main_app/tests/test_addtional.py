from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from main_app.models import Report
from main_app.serializers import ReportSerializer 

User = get_user_model()

# =============================================================================
# ADDITIONAL TESTS FOR 100% STATEMENT COVERAGE - REAL ARCHITECTURE
# =============================================================================

class SerializerAndModelCoverageTests(APITestCase):
    """
    Kelas pengujian tambahan untuk menaikkan coverage model dan serializer.
    """
    def setUp(self):
        self.warga = User.objects.create_user(
            username='warga_str_test',
            password='Password123!',
            is_staff=False
        )

    def test_report_model_str(self):
        """
        Menguji str(report) agar memanggil __str__ dan mengembalikan judul laporan.
        """
        report = Report.objects.create(
            title='Laporan Str Uji',
            category='Lainnya',
            description='Deskripsi',
            location='Lokasi',
            status='REPORTED',
            reporter=self.warga
        )
        self.assertEqual(str(report), 'Laporan Str Uji')

    def test_report_serializer_no_request_context(self):
        """
        Menguji serializer tanpa menyertakan request dalam context,
        sehingga reporter_name default dialihkan menjadi anonim.
        """
        report = Report.objects.create(
            title='Laporan Serializer Uji',
            category='Lainnya',
            description='Deskripsi',
            location='Lokasi',
            status='REPORTED',
            reporter=self.warga
        )
        serializer = ReportSerializer(report, context={})
        self.assertEqual(serializer.data['reporter_name'], 'Warga Anonim')


class MainAppMonolithicViewsCoverageTests(TestCase):
    """
    Menguji view fungsional terintegrasi di main_app/views.py / urls.py
    untuk mencakup alur dispatch, GET, POST, dan pengamanan hak akses.
    """
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_mono',
            password='Password123!',
            is_staff=True,
            is_superuser=True
        )
        self.citizen = User.objects.create_user(
            username='citizen_mono',
            password='Password123!',
            is_staff=False
        )
        self.report = Report.objects.create(
            title='Laporan Monolitik Uji',
            category='Infrastruktur',
            description='Ada kerusakan infrastruktur.',
            location='Bandung',
            status='REPORTED',
            reporter=self.citizen
        )

    def test_home_view_unauthenticated(self):
        """Menguji akses halaman home utama oleh user anonim"""
        response = self.client.get(reverse('backend_home_root'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_citizen(self):
        """Menguji akses halaman home utama oleh warga terautentikasi"""
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.get(reverse('backend_home_root'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_admin(self):
        """Menguji akses halaman home utama oleh petugas admin"""
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.get(reverse('backend_home_root'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_api_data_fetch(self):
        """Menguji endpoint penyuplai data chart analitik internal"""
        response = self.client.get(reverse('dashboard_api'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())
        self.assertIn('kategori', response.json())

    def test_report_create_view_unauthenticated(self):
        """Membuat aduan baru tanpa login harus dialihkan (302)"""
        response = self.client.post(reverse('tambah_laporan_frontend'), {
            'title': 'Aduan Gelap',
            'location': 'Kecamatan Kedondong'
        })
        self.assertEqual(response.status_code, 302)

    def test_report_create_view_citizen(self):
        """Membuat aduan baru dengan login warga valid"""
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.post(reverse('tambah_laporan_frontend'), {
            'title': 'Jalan Berlubang Kampus',
            'location': 'Polinela',
            'status': 'REPORTED'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Report.objects.filter(title='Jalan Berlubang Kampus').exists())

    def test_report_delete_view_unauthenticated(self):
        """Menghapus aduan tanpa login wajib ditolak dan diredirect"""
        response = self.client.get(reverse('hapus_laporan_frontend', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)

    def test_report_delete_view_citizen_denied(self):
        """Warga biasa dilarang keras menghapus data aduan publik"""
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.get(reverse('hapus_laporan_frontend', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)
        # Pastikan data tetap aman bertahta di database
        self.assertTrue(Report.objects.filter(id=self.report.id).exists())

    def test_report_delete_view_admin_success(self):
        """Admin memiliki wewenang penuh menghapus laporan keluhan"""
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.get(reverse('hapus_laporan_frontend', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Report.objects.filter(id=self.report.id).exists())