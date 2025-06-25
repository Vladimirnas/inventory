from django.urls import path
from . import views

urlpatterns = [
    # API для инвентаризации
    path('inventory/current/', views.current_inventory, name='api-inventory-current'),
    path('inventory/update_status/', views.update_inventory_status, name='api-inventory-update-status'),
] 