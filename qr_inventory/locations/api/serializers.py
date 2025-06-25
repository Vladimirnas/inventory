from rest_framework import serializers
from locations.models import Location
from assets.models import Asset


class LocationSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Location"""
    equipment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = ['id', 'name', 'qr_code', 'equipment_count', 'created_at']
        
    def get_equipment_count(self, obj):
        return obj.equipment_count()


class AssetSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Asset"""
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Asset
        fields = ['id', 'inventory_number', 'asset_name', 'quantity', 'responsible', 'department_name']
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else "Не указано" 