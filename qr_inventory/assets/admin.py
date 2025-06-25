from django.contrib import admin
from .models import Asset


class AssetAdmin(admin.ModelAdmin):
    list_display = ('inventory_number', 'asset_name', 'quantity', 'book_value', 'responsible', 'get_location_name', 'get_department_name', 'is_written_off')
    list_filter = ('is_written_off', 'year_of_manufacture', 'location', 'department')
    search_fields = ('inventory_number', 'asset_name', 'responsible', 'location__name', 'department__name')
    ordering = ('inventory_number',)
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else 'Не указано'
    get_department_name.short_description = 'Подразделение'


# class WrittenOffAssetAdmin(admin.ModelAdmin):
#     list_display = ('inventory_number', 'asset_name', 'quantity', 'book_value', 'responsible', 'location_name', 'department_name', 'write_off_date')
#     list_filter = ('write_off_date',)
#     search_fields = ('inventory_number', 'asset_name', 'responsible', 'location_name', 'department_name')
#     ordering = ('-write_off_date',)


admin.site.register(Asset, AssetAdmin)

 