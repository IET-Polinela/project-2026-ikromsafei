from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Report
from .serializers import ReportSerializer
from .permissions import IsOwnerAndDraftOrReadOnly

class ReportPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    pagination_class = ReportPagination

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerAndDraftOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        # Mengurutkan otomatis berdasarkan laporan terbaru (Lab 12)
        queryset = Report.objects.all().order_by('-updated_at')
        
        # Server Side Filtering menangkap parameter kueri URL ?tab= (Lab 12)
        tab = self.request.query_params.get('tab', None)
        if tab == 'my_reports':
            return queryset.filter(reporter=user)
        elif tab == 'feed':
            return queryset.filter(~Q(reporter=user) & ~Q(status='DRAFT'))
        
        # Default fallback untuk rekap status (Lab 12)
        return queryset.filter(~Q(status='DRAFT') | Q(status='DRAFT', reporter=user))

    def perform_create(self, serializer):
        # Menyimpan relasi reporter secara otomatis dari user session JWT (Lab 10)
        serializer.save(reporter=self.request.user)