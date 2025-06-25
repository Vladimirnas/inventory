import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os

from .models import Location
from .forms import LocationForm, AssignEquipmentForm
from assets.models import Asset


@login_required
def location_list(request):
    """Список всех помещений с QR-кодами"""
    locations = Location.objects.all()
    return render(request, 'locations/location_list.html', {
        'locations': locations
    })


@login_required
def location_detail(request, pk):
    """Детальный просмотр помещения"""
    location = get_object_or_404(Location, pk=pk)
    equipment = location.get_active_equipment()
    
    # Форма для назначения оборудования в помещение
    form = AssignEquipmentForm(initial={'location_id': location.id})
    
    return render(request, 'locations/location_detail.html', {
        'location': location,
        'equipment': equipment,
        'form': form
    })


@login_required
def create_location(request):
    """Создание нового помещения с QR-кодом"""
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Создано новое помещение: {location.name}')
            return redirect('location_list')
    else:
        form = LocationForm()
    
    return render(request, 'locations/create_location.html', {
        'form': form
    })


@login_required
def delete_location(request, pk):
    """Удаление помещения"""
    location = get_object_or_404(Location, pk=pk)
    
    if request.method == 'POST':
        location_name = location.name
        location.delete()
        messages.success(request, f'Помещение "{location_name}" успешно удалено')
        return redirect('location_list')
        
    return render(request, 'locations/delete_location.html', {
        'location': location
    })


@login_required
def print_location_qr_codes(request):
    """Печать QR-кодов для помещений"""
    # Проверяем, есть ли параметр ids для печати выбранных QR-кодов
    location_ids = request.GET.get('ids')
    
    if location_ids:
        ids_list = [int(id) for id in location_ids.split(',')]
        locations = Location.objects.filter(id__in=ids_list)
    else:
        locations = Location.objects.all()
        
    return render(request, 'locations/print_qr_codes.html', {
        'locations': locations
    })


@login_required
def assign_equipment(request, pk):
    """Назначение оборудования в помещение"""
    location = get_object_or_404(Location, pk=pk)
    
    if request.method == 'POST':
        form = AssignEquipmentForm(request.POST)
        if form.is_valid():
            inventory_number = form.cleaned_data['inventory_number']
            
            try:
                asset = Asset.objects.get(inventory_number=inventory_number, is_written_off=False)
                asset.location = location
                asset.storage_location = location.name
                asset.save()
                
                messages.success(request, f'Оборудование "{asset.asset_name}" перемещено в помещение "{location.name}"')
            except Asset.DoesNotExist:
                messages.error(request, f'Оборудование с инвентарным номером {inventory_number} не найдено')
                
            return redirect('location_detail', pk=location.id)
    
    # Если GET-запрос или ошибка валидации, возвращаем на страницу детального просмотра
    return redirect('location_detail', pk=location.id)


@login_required
def remove_equipment(request, location_pk, asset_pk):
    """Удаление оборудования из помещения"""
    location = get_object_or_404(Location, pk=location_pk)
    asset = get_object_or_404(Asset, pk=asset_pk)
    
    if asset.location == location:
        asset.location = None
        asset.storage_location = ''
        asset.save()
        messages.success(request, f'Оборудование "{asset.asset_name}" удалено из помещения "{location.name}"')
    else:
        messages.error(request, 'Оборудование не принадлежит данному помещению')
        
    return redirect('location_detail', pk=location_pk)


@csrf_exempt
def location_info(request, qr_code):
    """API для получения информации о помещении по QR-коду"""
    try:
        location = Location.objects.get(qr_code=qr_code)
        return JsonResponse({
            'id': location.id,
            'name': location.name,
            'qr_code': location.qr_code,
            'equipment_count': location.equipment_count()
        })
    except Location.DoesNotExist:
        return JsonResponse({'error': 'Помещение не найдено'}, status=404)


@csrf_exempt
def location_equipment(request, qr_code):
    """API для получения списка оборудования в помещении по QR-коду"""
    try:
        location = Location.objects.get(qr_code=qr_code)
        equipment = location.get_active_equipment()
        
        equipment_list = [{
            'id': item.id,
            'inventory_number': item.inventory_number,
            'asset_name': item.asset_name,
            'quantity': item.quantity,
            'responsible': item.responsible
        } for item in equipment]
        
        return JsonResponse(equipment_list, safe=False)
    except Location.DoesNotExist:
        return JsonResponse({'error': 'Помещение не найдено'}, status=404) 