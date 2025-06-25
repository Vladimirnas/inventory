from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from inventory.models import Inventory, InventoryItem
from locations.models import Location
from assets.models import Asset

class InventoryItemSerializer:
    @staticmethod
    def to_representation(item):
        """Сериализует InventoryItem в словарь"""
        return {
            'id': item.id,
            'inventoryNumber': item.asset.inventory_number,
            'assetName': item.asset.asset_name,
            'quantity': item.asset.quantity,
            'scannedQuantity': item.scanned_quantity,
            'status': item.inventory_status,
            'location': item.asset.get_location_name() if hasattr(item.asset, 'get_location_name') and item.asset.location else None,
            'tableId': item.inventory.table_name if hasattr(item.inventory, 'table_name') else str(item.inventory.id),
        }

@api_view(['GET'])
def current_inventory(request):
    """
    API для получения текущей инвентаризации
    Может принимать параметр location_qr для фильтрации по QR-коду помещения
    """
    # Получаем текущую активную инвентаризацию
    try:
        active_inventory = Inventory.objects.filter(status='active').latest('start_date')
    except Inventory.DoesNotExist:
        return Response({'error': 'Нет активной инвентаризации'}, status=status.HTTP_404_NOT_FOUND)
    
    # Фильтрация по помещению, если указан QR-код
    location_qr = request.query_params.get('location_qr')
    
    if location_qr:
        try:
            location = Location.objects.get(qr_code=location_qr)
            inventory_items = InventoryItem.objects.filter(
                inventory=active_inventory,
                asset__location=location
            )
        except Location.DoesNotExist:
            return Response({'error': 'QR-код помещения не найден'}, status=status.HTTP_404_NOT_FOUND)
    else:
        inventory_items = InventoryItem.objects.filter(inventory=active_inventory)
    
    # Сериализуем данные
    serialized_items = [InventoryItemSerializer.to_representation(item) for item in inventory_items]
    
    return Response(serialized_items)

@api_view(['POST'])
def update_inventory_status(request):
    """API для обновления статуса инвентаризационной позиции"""
    item_id = request.data.get('itemId')
    status_value = request.data.get('status')
    table_id = request.data.get('tableId')
    
    if not all([item_id, status_value, table_id]):
        return Response({'error': 'Не указаны обязательные параметры'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Находим инвентаризацию по имени таблицы или ID
        try:
            inventory = Inventory.objects.get(table_name=table_id)
        except (Inventory.DoesNotExist, AttributeError):
            # Если table_name не существует или не найден, пробуем искать по ID
            inventory = Inventory.objects.get(id=table_id)
            
        # Находим элемент инвентаризации
        item = InventoryItem.objects.get(id=item_id, inventory=inventory)
        
        # Обновляем статус
        item.inventory_status = status_value
        
        # Если статус "found", устанавливаем scanned_quantity равным quantity
        if status_value == 'completed':
            item.scanned_quantity = item.total_quantity
        else:
            item.scanned_quantity = 0
            
        item.save()
        
        return Response({'success': True})
    except Inventory.DoesNotExist:
        return Response({'error': 'Инвентаризация не найдена'}, status=status.HTTP_404_NOT_FOUND)
    except InventoryItem.DoesNotExist:
        return Response({'error': 'Элемент инвентаризации не найден'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 