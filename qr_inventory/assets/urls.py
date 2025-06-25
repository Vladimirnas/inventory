from django.urls import path
from . import views

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('add/', views.add_property, name='add_property'),
    path('edit/<int:pk>/', views.edit_property, name='edit_property'),
    path('detail/<int:pk>/', views.property_detail, name='property_detail'),
    path('upload-csv/', views.upload_csv, name='upload_csv'),
    path('download-csv/', views.download_csv, name='download_csv'),
    path('write-off/<int:pk>/', views.write_off_asset, name='write_off_asset'),
    path('written-off-history/', views.written_off_history, name='written_off_history'),
    path('update-responsible/', views.update_responsible, name='update_responsible'),
    path('print-qr-codes/', views.print_asset_qr_codes, name='print_asset_qr_codes'),
] 