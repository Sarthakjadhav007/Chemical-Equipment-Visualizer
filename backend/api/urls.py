from django.urls import path
from .views import UploadCSVView, DataSummaryView, HistoryView, GeneratePDFView

urlpatterns = [
    path('upload/', UploadCSVView.as_view(), name='api-upload'),
    path('summary/', DataSummaryView.as_view(), name='api-summary'),
    path('summary/<int:pk>/', DataSummaryView.as_view(), name='api-summary-detail'),
    path('history/', HistoryView.as_view(), name='api-history'),
    path('pdf/<int:pk>/', GeneratePDFView.as_view(), name='api-pdf'),
]
