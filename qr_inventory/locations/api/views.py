from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from locations.models import Location
from assets.models import Asset
from .serializers import LocationSerializer, AssetSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def location_list(request):
    """API для получения списка всех помещений"""
    locations = Location.objects.all()
    serializer = LocationSerializer(locations, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def location_detail(request, pk):
    """API для получения информации о конкретном помещении"""
    try:
        location = Location.objects.get(pk=pk)
        serializer = LocationSerializer(location)
        return Response(serializer.data)
    except Location.DoesNotExist:
        return Response({'error': 'Помещение не найдено'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def location_equipment(request, pk):
    """API для получения списка оборудования в помещении"""
    try:
        location = Location.objects.get(pk=pk)
        equipment = location.get_active_equipment()
        serializer = AssetSerializer(equipment, many=True)
        return Response(serializer.data)
    except Location.DoesNotExist:
        return Response({'error': 'Помещение не найдено'}, status=status.HTTP_404_NOT_FOUND)


class LocationQRView(APIView):
    """API для работы с QR-кодами помещений"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Создание нового помещения с QR-кодом"""
        location_name = request.data.get('locationName')
        
        if not location_name:
            return Response({'error': 'Название помещения не указано'}, status=status.HTTP_400_BAD_REQUEST)
            
        location = Location.objects.create(name=location_name)
        serializer = LocationSerializer(location)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def delete(self, request, pk):
        """Удаление помещения по ID"""
        try:
            location = Location.objects.get(pk=pk)
            location_name = location.name
            location.delete()
            return Response({
                'success': True,
                'message': f'Помещение "{location_name}" успешно удалено'
            })
        except Location.DoesNotExist:
            return Response({'error': 'Помещение не найдено'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def scan_location_qr(request, qr_code):
    """API для сканирования QR-кода помещения (доступно без аутентификации)"""
    try:
        location = Location.objects.get(qr_code=qr_code)
        serializer = LocationSerializer(location)
        return Response(serializer.data)
    except Location.DoesNotExist:
        return Response({'error': 'QR-код не найден'}, status=status.HTTP_404_NOT_FOUND) 