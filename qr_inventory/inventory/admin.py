from django.contrib import admin
from .models import Inventory, InventoryItem, Department


class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    extra = 0
    readonly_fields = ('asset', 'total_quantity', 'scanned_quantity', 'inventory_status', 'last_scanned')
    can_delete = False
    fields = ('asset', 'total_quantity', 'scanned_quantity', 'inventory_status', 'last_scanned')


class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'inventory_type', 'status', 'items_count')
    list_filter = ('status', 'inventory_type', 'start_date')
    search_fields = ('name',)
    readonly_fields = ('date_completed',)
    inlines = [InventoryItemInline]


class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'asset', 'total_quantity', 'scanned_quantity', 'inventory_status', 'last_scanned')
    list_filter = ('inventory_status', 'inventory')
    search_fields = ('asset__inventory_number', 'asset__asset_name')
    readonly_fields = ('last_scanned',)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'get_employees_count')
    search_fields = ('name', 'code')
    
    def get_employees_count(self, obj):
        return obj.employees.count()
    
    get_employees_count.short_description = 'Число сотрудников'


admin.site.register(Inventory, InventoryAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)
admin.site.register(Department, DepartmentAdmin)
