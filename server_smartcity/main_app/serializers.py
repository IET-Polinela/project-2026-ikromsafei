from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    # Tambahkan dua field custom ini agar terbaca di test
    reporter = serializers.SerializerMethodField()
    reporter_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = '__all__' # Atau pastikan ada 'reporter' dan 'reporter_name'

    def get_reporter(self, obj):
        # Memaksa teks keluar sebagai "Warga Anonim" di feed publik
        return "Warga Anonim"

    def get_reporter_name(self, obj):
        request = self.context.get('request')
        # Jika diakses pemiliknya sendiri, tampilkan nama asli, jika orang lain tampilkan Anonim
        if request and request.user == obj.reporter:
            return obj.reporter.username
        return "Warga Anonim"