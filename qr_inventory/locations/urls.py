from django.urls import path
from . import views

urlpatterns = [
    path('', views.location_list, name='location_list'),
    path('<int:pk>/', views.location_detail, name='location_detail'),
    path('create/', views.create_location, name='create_location'),
    path('delete/<int:pk>/', views.delete_location, name='delete_location'),
    path('print-qr-codes/', views.print_location_qr_codes, name='print_location_qr_codes'),
    path('<int:pk>/assign-equipment/', views.assign_equipment, name='assign_equipment'),
    path('<int:location_pk>/remove-equipment/<int:asset_pk>/', views.remove_equipment, name='remove_equipment'),
    
    # API для мобильного приложения
    path('api/info/<str:qr_code>/', views.location_info, name='location_info'),
    path('api/equipment/<str:qr_code>/', views.location_equipment, name='location_equipment'),
] 