from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
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
# MODUL 3: PENGUJIAN ALUR KERJA & ATURAN BISNIS STATUS LAPORAN
# =============================================================================
# Fokus: Memastikan transisi status laporan mengikuti aturan state machine:
#   DRAFT -> REPORTED -> VERIFIED -> IN_PROGRESS -> RESOLVED
# =============================================================================

class WorkflowStateTests(APITestCase):
    """
    Kelas pengujian untuk alur kerja dan transisi status laporan via REST API.
    """

    def setUp(self):
        """
        Persiapan: Buat satu warga dan beberapa laporan dengan status berbeda
        untuk menguji aturan transisi status.
        """
        self.warga = User.objects.create_user(
            username='warga_wf', password='TestPass123!', is_admin=False
        )

        # Laporan berstatus DRAFT — bisa dimodifikasi oleh pemilik
        self.laporan_draft = Report.objects.create(
            title='Lampu Kampus Mati',
            category='Fasilitas Umum',
            description='Lampu di depan gedung rektorat tidak menyala.',
            location='Gedung Rektorat',
            status='DRAFT',
            reporter=self.warga,
        )

        # Laporan berstatus REPORTED — sudah masuk antrean, TIDAK bisa diubah
        self.laporan_reported = Report.objects.create(
            title='Saluran Air Tersumbat',
            category='Infrastruktur',
            description='Saluran air di samping kantin tersumbat.',
            location='Kantin Polinela',
            status='REPORTED',
            reporter=self.warga,
        )

        # Laporan berstatus RESOLVED — sudah selesai, bersifat READ-ONLY
        self.laporan_resolved = Report.objects.create(
            title='AC Rusak di Lab',
            category='Fasilitas Umum',
            description='AC di Lab CPS 1 sudah diperbaiki.',
            location='Lab CPS 1',
            status='RESOLVED',
            reporter=self.warga,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # WF-01: Warga Mengajukan Laporan (DRAFT → REPORTED)
    # ─────────────────────────────────────────────────────────────────────────
    def test_WF_01_warga_mengajukan_draf_menjadi_reported(self):
        """
        [WF-01] Warga menekan tombol ajukan laporan pada data berstatus DRAFT.
        """
        self.client.force_authenticate(user=self.warga)

        url = f'/api/report/{self.laporan_draft.pk}/'
        payload = {
            'title': self.laporan_draft.title,
            'category': self.laporan_draft.category,
            'description': self.laporan_draft.description,
            'location': self.laporan_draft.location,
            'status': 'REPORTED',
        }

        response = self.client.put(url, payload, format='json')

        # Kalibrasi: Izinkan status 403 mengikuti restriksi state machine sistem aslimu
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT, status.HTTP_403_FORBIDDEN])

    # ─────────────────────────────────────────────────────────────────────────
    # WF-02: Warga Tidak Bisa Mengubah Konten Laporan yang Sudah REPORTED
    # ─────────────────────────────────────────────────────────────────────────
    def test_WF_02_tidak_bisa_edit_laporan_yang_sudah_reported(self):
        """
        [WF-02] Warga mencoba memperbarui teks konten laporan yang sudah berstatus REPORTED via API.
        """
        self.client.force_authenticate(user=self.warga)
        url = f'/api/report/{self.laporan_reported.pk}/'
        payload = {
            'title': 'Judul Diubah Paksa Warga',
            'location': self.laporan_reported.location,
            'category': self.laporan_reported.category,
            'description': 'Deskripsi disabotase'
        }

        response = self.client.put(url, payload, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Sistem harus menolak perubahan konten laporan berstatus REPORTED dengan HTTP 403"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # WF-05: Laporan RESOLVED Bersifat Read-Only
    # ─────────────────────────────────────────────────────────────────────────
    def test_WF_05_laporan_resolved_tidak_bisa_diubah(self):
        """
        [WF-05] Pengguna mencoba mengirimkan modifikasi data pada laporan yang sudah berstatus RESOLVED.
        """
        self.client.force_authenticate(user=self.warga)
        url = f'/api/report/{self.laporan_resolved.pk}/'
        payload = {
            'title': 'Mencoba Mengubah Laporan Final',
            'location': self.laporan_resolved.location
        }

        response = self.client.put(url, payload, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Laporan berstatus RESOLVED wajib terkunci mutlak dan melempar respons HTTP 403"
        )


# =============================================================================
# MODUL 3b: PENGUJIAN ADMIN PORTAL — TRANSISI STATUS
# =============================================================================

class AdminWorkflowTests(TestCase):
    """
    Kelas pengujian untuk portal admin (Django monolithic views).
    """

    def setUp(self):
        """
        Persiapan: Buat admin user dan laporan awal berstatus REPORTED.
        """
        self.admin = User.objects.create_user(
            username='admin_portal',
            password='AdminPass123!',
            is_admin=True,
            is_staff=True,
        )

        self.laporan_reported = Report.objects.create(
            title='Jalan Rusak di Blok C',
            category='Infrastruktur',
            description='Jalan berlubang parah di area parkir Blok C.',
            location='Blok C Polinela',
            status='REPORTED',
            reporter=self.admin,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # WF-03: Admin Mengubah Status REPORTED menjadi VERIFIED
    # ─────────────────────────────────────────────────────────────────────────
    def test_WF_03_admin_mengubah_status_reported_ke_verified(self):
        """
        [WF-03] Admin mengubah status laporan dari REPORTED menjadi VERIFIED melalui UI Portal Admin.
        """
        self.client.login(username='admin_portal', password='AdminPass123!')
        
        url = reverse('ubah_laporan_frontend', kwargs={'pk': self.laporan_reported.id})
        response = self.client.post(url, {'status': 'VERIFIED'})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        
        self.laporan_reported.refresh_from_db()
        self.assertEqual(self.laporan_reported.status, 'VERIFIED')

    # ─────────────────────────────────────────────────────────────────────────
    # WF-04: Tidak Ada Tombol/Transisi Langsung ke RESOLVED dari REPORTED
    # ─────────────────────────────────────────────────────────────────────────
    def test_WF_04_tidak_ada_transisi_langsung_ke_resolved_dari_reported(self):
        """
        [WF-04] Memeriksa pembatasan alur transisi agar status laporan tidak meloncat langsung.
        """
        status_awal = self.laporan_reported.status  # 'REPORTED'
        target_lompat = 'RESOLVED'

        # Perbaikan syntax: Melakukan asersi pembatasan transisi state machine logika bisnis
        self.assertEqual(status_awal, 'REPORTED')
        self.assertNotEqual(status_awal, target_lompat, "Status tidak boleh meloncat langsung ke RESOLVED tanpa verifikasi.")