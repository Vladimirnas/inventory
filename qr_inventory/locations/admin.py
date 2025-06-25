from django.contrib import admin
from .models import Location


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'qr_code', 'equipment_count', 'created_at')
    search_fields = ('name', 'qr_code')
    ordering = ('name',)
    readonly_fields = ('qr_code', 'qr_image', 'created_at', 'updated_at')


admin.site.register(Location, LocationAdmin) 