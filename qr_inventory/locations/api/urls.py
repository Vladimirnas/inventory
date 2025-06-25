from django.urls import path
from . import views

urlpatterns = [
    # API для работы с помещениями
    path('locations/', views.location_list, name='api-location-list'),
    path('locations/<int:pk>/', views.location_detail, name='api-location-detail'),
    path('locations/<int:pk>/equipment/', views.location_equipment, name='api-location-equipment'),
    
    # API для QR-кодов помещений
    path('location-qr/', views.LocationQRView.as_view(), name='api-location-qr-create'),
    path('location-qr/<int:pk>/', views.LocationQRView.as_view(), name='api-location-qr-delete'),
    path('location-qr/equipment/<int:pk>/', views.location_equipment, name='api-location-qr-equipment'),
    
    # API для сканирования QR-кодов (без аутентификации)
    path('scan/location/<str:qr_code>/', views.scan_location_qr, name='api-scan-location-qr'),
] 