import random
from django.core.management.base import BaseCommand
from faker import Faker
from main_app.models import Report

class Command(BaseCommand):
    help = 'Generate fake data laporan permasalahan kota secara kontekstual'

    def add_arguments(self, parser):
        parser.add_argument('num_records', type=int, help='Jumlah rekord data yang ingin dibuat')

    def handle(self, *args, **kwargs):
        num_records = kwargs['num_records']
        fake = Faker('id_ID')
        
        categories = ['Jalan Rusak', 'Sampah', 'Lampu Mati', 'Drainase', 'Keamanan']
        status_choices = ['REPORTED', 'VERIFIED', 'IN_PROGRESS', 'RESOLVED']

        for _ in range(num_records):
            Report.objects.create(
                title=f"Isu {random.choice(categories)} - {fake.street_name()}",
                category=random.choice(categories),
                description=f"Warga melaporkan kendala infrastruktur. Mohon untuk segera diatasi.",
                location=f"Kecamatan {fake.city()}, {fake.address()}",
                status=random.choice(status_choices)
            )
        self.stdout.write(self.style.SUCCESS(f'Berhasil membuat {num_records} laporan dinamis!'))