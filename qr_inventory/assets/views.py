import csv
import io
import qrcode
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models.functions import Lower
from .models import Asset
from locations.models import Location
from .forms import AssetForm, UploadCSVForm, WriteOffAssetForm, UpdateResponsibleForm


@login_required
def property_list(request):
    """Отображение списка имущества"""
    search_query = request.GET.get('search', '')
    sort_column = request.GET.get('sort')
    sort_direction = request.GET.get('direction', 'asc')
    
    # Проверяем, является ли пользователь администратором
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Получаем подразделение пользователя
    try:
        user_profile = request.user.profile
        department = user_profile.department
    except:
        user_profile = None
        department = None
    
    # Базовая фильтрация
    assets_query = Asset.objects.filter(is_written_off=False)
    
    # Фильтрация по подразделению, если пользователь не администратор и у него есть подразделение
    if not is_admin and department:
        assets_query = assets_query.filter(department=department)
    
    # Поиск
    if search_query:
        search_query_lower = search_query.lower()
        search_query_title = search_query.title()
        assets_query = assets_query.filter(
            Q(inventory_number__icontains=search_query) | 
            Q(asset_name__contains=search_query) |
            Q(asset_name__contains=search_query_lower) |
            Q(asset_name__contains=search_query_title) |
            Q(responsible__icontains=search_query) |
            Q(location__name__icontains=search_query)
        )
    
    # Сортировка
    if sort_column:
        # Маппинг полей сортировки
        sort_fields = {
            'inventory_number': 'inventory_number',
            'asset_name': 'asset_name',
            'quantity': 'quantity',
            'book_value': 'book_value',
            'responsible': 'responsible',
            'location': 'location__name',
            'department': 'department__name'
        }
        
        if sort_column in sort_fields:
            order_field = sort_fields[sort_column]
            if sort_direction == 'desc':
                order_field = f'-{order_field}'
            assets_query = assets_query.order_by(order_field)
    
    paginator = Paginator(assets_query, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'assets/property_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_assets': assets_query.count(),
        'is_admin': is_admin,
        'user_department': department.name if department else 'Не указано',
        'sort_column': sort_column,
        'sort_direction': sort_direction
    })


@login_required
def add_property(request):
    """Добавление нового имущества"""
    # Проверяем, является ли пользователь администратором
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Получаем подразделение пользователя
    try:
        user_profile = request.user.profile
        department = user_profile.department
    except:
        user_profile = None
        department = None
    
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES, is_admin=is_admin, user_department=department)
        if form.is_valid():
            asset = form.save(commit=False)
            
            # Если пользователь не админ и у него есть подразделение,
            # автоматически устанавливаем подразделение для имущества
            if not is_admin and department:
                asset.department = department
                
            asset.save()
            
            # Генерируем QR-код
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f'assetId={asset.id}')
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Сохраняем QR-код
            buffer = BytesIO()
            img.save(buffer)
            buffer.seek(0)
            
            filename = f'asset_{asset.inventory_number}.png'
            asset.qr_image.save(filename, ContentFile(buffer.read()), save=True)
            asset.qr_code = f'assetId={asset.id}'
            asset.save()
            
            messages.success(request, f'Имущество "{asset.asset_name}" успешно добавлено.')
            return redirect('property_list')
    else:
        # Для не-администраторов предварительно заполняем поле отдела
        initial_data = {}
        if not is_admin and department:
            initial_data['department'] = department
        form = AssetForm(initial=initial_data, is_admin=is_admin, user_department=department)
    
    return render(request, 'assets/add_property.html', {
        'form': form,
        'is_admin': is_admin,
        'user_department': department
    })


@login_required
def edit_property(request, pk):
    """Редактирование имущества"""
    asset = get_object_or_404(Asset, pk=pk, is_written_off=False)
    
    # Проверяем, является ли пользователь администратором
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Получаем подразделение пользователя
    try:
        user_profile = request.user.profile
        department = user_profile.department
    except:
        user_profile = None
        department = None
    
    # Проверка доступа: администраторы могут редактировать всё имущество,
    # обычные пользователи - только имущество своего подразделения
    if not is_admin and department and asset.department != department:
        messages.error(request, 'У вас нет доступа к редактированию этого имущества.')
        return redirect('property_list')
    
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES, instance=asset, is_admin=is_admin, user_department=department)
        if form.is_valid():
            form.save()
            messages.success(request, f'Имущество "{asset.asset_name}" успешно обновлено.')
            return redirect('property_list')
    else:
        form = AssetForm(instance=asset, is_admin=is_admin, user_department=department)
    
    return render(request, 'assets/edit_property.html', {'form': form, 'asset': asset})


@login_required
def property_detail(request, pk):
    """Просмотр информации об имуществе"""
    asset = get_object_or_404(Asset, pk=pk)
    
    # Проверяем, является ли пользователь администратором
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Получаем подразделение пользователя
    try:
        user_profile = request.user.profile
        department = user_profile.department
    except:
        user_profile = None
        department = None
    
    # Проверка доступа: администраторы могут видеть всё имущество,
    # обычные пользователи - только имущество своего подразделения
    if not is_admin and department and asset.department != department:
        messages.error(request, 'У вас нет доступа к этому имуществу.')
        return redirect('property_list')
    
    return render(request, 'assets/property_detail.html', {'asset': asset})


@login_required
def upload_csv(request):
    """Загрузка CSV файла с имуществом"""
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Файл должен быть в формате CSV.')
                return redirect('upload_csv')
            
            # Обработка CSV файла
            try:
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string, delimiter=',', quotechar='"')
                next(reader)  # Пропускаем заголовок
                
                count = 0
                for row in reader:
                    inventory_number = row[0]
                    asset_name = row[1]
                    quantity = int(row[2]) if row[2] else 1
                    book_value = float(row[3]) if row[3] else None
                    responsible = row[4] if row[4] else None
                    location_name = row[5] if row[5] else None
                    year_of_manufacture = int(row[6]) if row[6] else None
                    
                    # Если указано местоположение, создаем или получаем его
                    location = None
                    if location_name:
                        location, created = Location.objects.get_or_create(name=location_name)
                    
                    # Проверяем существование имущества
                    asset, created = Asset.objects.update_or_create(
                        inventory_number=inventory_number,
                        defaults={
                            'asset_name': asset_name,
                            'quantity': quantity,
                            'book_value': book_value,
                            'responsible': responsible,
                            'location': location,
                            'year_of_manufacture': year_of_manufacture,
                        }
                    )
                    
                    # Если создан новый актив, генерируем QR-код
                    if created:
                        qr_data = inventory_number
                        qr = qrcode.QRCode(
                            version=1,
                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                            box_size=10,
                            border=4,
                        )
                        qr.add_data(qr_data)
                        qr.make(fit=True)
                        
                        img = qr.make_image(fill_color="black", back_color="white")
                        buffer = BytesIO()
                        img.save(buffer, format='PNG')
                        
                        filename = f'asset_{inventory_number.replace("/", "_")}.png'
                        asset.qr_code = qr_data
                        asset.qr_image.save(filename, ContentFile(buffer.getvalue()), save=False)
                        asset.save()
                    
                    count += 1
                
                messages.success(request, f'Успешно обработано {count} записей.')
                return redirect('property_list')
                
            except Exception as e:
                messages.error(request, f'Ошибка при обработке CSV файла: {str(e)}')
                return redirect('upload_csv')
    else:
        form = UploadCSVForm()
    
    return render(request, 'assets/upload_csv.html', {'form': form})


@login_required
def download_csv(request):
    """Загрузка CSV файла со списком имущества"""
    # Проверяем, является ли пользователь администратором
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Получаем подразделение пользователя
    try:
        user_profile = request.user.profile
        department = user_profile.department
    except:
        user_profile = None
        department = None
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Инвентарный номер', 'Наименование', 'Количество', 'Балансовая стоимость',
        'Ответственный', 'Помещение', 'Подразделение', 'Год выпуска'
    ])
    
    # Формируем запрос с учетом подразделения для неадминистраторов
    assets_query = Asset.objects.filter(is_written_off=False)
    if not is_admin and department:
        assets_query = assets_query.filter(department=department)
    
    for asset in assets_query:
        writer.writerow([
            asset.inventory_number,
            asset.asset_name,
            asset.quantity,
            asset.book_value,
            asset.responsible or '',
            asset.get_location_name(),
            asset.department.name if asset.department else '',
            asset.year_of_manufacture or ''
        ])
    
    return response


# @login_required
# def write_off_asset(request, pk):
#     """Списание имущества"""
#     asset = get_object_or_404(Asset, pk=pk, is_written_off=False)
    
#     # Проверяем, является ли пользователь администратором
#     is_admin = request.user.is_staff or request.user.is_superuser
    
#     # Получаем подразделение пользователя
#     try:
#         user_profile = request.user.profile
#         department = user_profile.department
#     except:
#         user_profile = None
#         department = None
    
#     # Проверка доступа: администраторы могут списывать всё имущество,
#     # обычные пользователи - только имущество своего подразделения
#     if not is_admin and department and asset.department != department:
#         messages.error(request, 'У вас нет доступа к списанию этого имущества.')
#         return redirect('property_list')
    
#     if request.method == 'POST':
#         form = WriteOffAssetForm(request.POST)
#         if form.is_valid():
#             # Создаем запись о списанном имуществе
#             write_off_record = WrittenOffAsset(
#                 inventory_number=asset.inventory_number,
#                 asset_name=asset.asset_name,
#                 quantity=asset.quantity,
#                 book_value=asset.book_value,
#                 responsible=asset.responsible,
#                 location_name=asset.get_location_name(),
#                 department_name=asset.department.name if asset.department else None,
#                 year_of_manufacture=asset.year_of_manufacture,
#                 photo_link=asset.photo.url if asset.photo else None,
#                 write_off_date=timezone.now()
#             )
#             write_off_record.save()
            
#             # Списываем имущество
#             asset.write_off()
            
#             messages.success(request, f'Имущество "{asset.asset_name}" успешно списано.')
#             return redirect('property_list')
#     else:
#         form = WriteOffAssetForm(initial={'asset_id': asset.id})
    
#     return render(request, 'assets/write_off_asset.html', {'form': form, 'asset': asset})


# @login_required
# def written_off_history(request):
#     """История списаний"""
#     # Проверяем, является ли пользователь администратором
#     is_admin = request.user.is_staff or request.user.is_superuser
    
#     # Получаем подразделение пользователя
#     try:
#         user_profile = request.user.profile
#         department = user_profile.department
#     except:
#         user_profile = None
#         department = None
    
#     # Формируем запрос с учетом подразделения для неадминистраторов
#     history_query = WrittenOffAsset.objects.all()
#     if not is_admin and department:
#         history_query = history_query.filter(department_name=department.name)
    
#     # Добавляем пагинацию
#     paginator = Paginator(history_query, 20)  # 20 записей на страницу
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
#     return render(request, 'assets/written_off_history.html', {
#         'page_obj': page_obj,
#         'items': page_obj  # для обратной совместимости
#     })



@login_required
def write_off_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk, is_written_off=False)

    is_admin = request.user.is_staff or request.user.is_superuser
    try:
        department = request.user.profile.department
    except:
        department = None

    if not is_admin and department and asset.department != department:
        messages.error(request, 'У вас нет доступа к списанию этого имущества.')
        return redirect('property_list')

    if request.method == 'POST':
        form = WriteOffAssetForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data['quantity']
            asset.write_off_quantity(qty)
            messages.success(request, f'Списано {qty} шт. имущества "{asset.asset_name}".')
            return redirect('property_list')
    else:
        form = WriteOffAssetForm(initial={'asset_id': asset.id})

    return render(request, 'assets/write_off_asset.html', {'form': form, 'asset': asset})




@login_required
def written_off_history(request):
    """История списанного имущества"""
    is_admin = request.user.is_staff or request.user.is_superuser

    try:
        department = request.user.profile.department
    except:
        department = None

    assets = Asset.objects.filter(total_written_off__gt=0)

    if not is_admin and department:
        assets = assets.filter(department=department)

    paginator = Paginator(assets.order_by('-write_off_date'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'assets/written_off_history.html', {
        'page_obj': page_obj,
        'items': page_obj  # если шаблон использует items
    })


@login_required
def update_responsible(request):
    """Обновление ответственного за имущество"""
    if request.method == 'POST':
        form = UpdateResponsibleForm(request.POST)
        if form.is_valid():
            asset_id = form.cleaned_data['asset_id']
            responsible = form.cleaned_data['responsible']
            
            asset = get_object_or_404(Asset, pk=asset_id, is_written_off=False)
            asset.responsible = responsible
            asset.save()
            
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Метод не поддерживается'})


@login_required
def print_asset_qr_codes(request):
    """Печать QR-кодов имущества"""
    asset_ids = request.GET.get('ids', '')
    
    if asset_ids:
        ids_list = asset_ids.split(',')
        items = Asset.objects.filter(id__in=ids_list, is_written_off=False)
    else:
        items = Asset.objects.filter(is_written_off=False)
    
    return render(request, 'assets/print_asset_qr_codes.html', {'items': items}) 