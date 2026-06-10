from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    # KUNCI UTAMA: Supaya field user otomatis terisi oleh sistem dan tidak menolak inputan warga
    user = serializers.ReadOnlyField(source='user.username') 

    class Meta:
        model = Report
        fields = '__all__'