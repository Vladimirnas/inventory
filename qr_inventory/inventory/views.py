import os
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.template.loader import render_to_string
from django.db.models import F
from datetime import date, datetime
from weasyprint import HTML
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
from fpdf import FPDF
from django.conf import settings




from .models import Inventory, InventoryItem, Department
from .forms import (
    PlannedInventoryForm, UnplannedInventoryForm, CompleteInventoryForm,
    DepartmentForm, UserEditForm
)
from assets.models import Asset
from accounts.models import UserProfile
from accounts.forms import RegisterForm
from .utils import department_access_required

# Функция перенаправления закрытых административных URL
def admin_redirect(request, pk=None):
    """
    Перенаправляет все запросы на административные URL на главную страницу с сообщением
    о том, что администрирование доступно только через Django Admin.
    """
    
    return redirect('/')


@login_required
def inventory_home(request):
    """Главная страница инвентаризации"""
    # Проверяем профиль пользователя
    try:
        user_profile = request.user.profile
        is_admin = request.user.is_staff or request.user.is_superuser
    except:
        user_profile = None
        is_admin = False
    
    # Проверяем, есть ли активная инвентаризация
    has_active_inventory = False
    
    if is_admin:
        # Администратор видит все активные инвентаризации
        has_active_inventory = Inventory.objects.filter(status='active').exists()
    else:
        # Обычный пользователь видит только инвентаризации своего подразделения
        if user_profile and user_profile.department:
            has_active_inventory = Inventory.objects.filter(
                status='active', 
                department=user_profile.department
            ).exists()
    
    return render(request, 'inventory/inventory.html', {
        'has_active_inventory': has_active_inventory
    })


@login_required
def planned_inventory(request):
    """Плановая инвентаризация"""
    # Проверяем, есть ли активная инвентаризация
    has_active = check_active_inventory(request)
    if has_active:
        messages.warning(request, 'Невозможно начать новую инвентаризацию, пока не завершена текущая.')
        return redirect('inventory_home')
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        
        if start_date:
            # Получаем подразделение пользователя
            try:
                user_profile = request.user.profile
                department = user_profile.department
            except:
                user_profile = None
                department = None
            
            # Создаем новую инвентаризацию
            inventory = Inventory(
                name=f'Плановая инвентаризация от {start_date}',
                start_date=start_date,
                inventory_type='planned',
                status='active',
                department=department,
                created_by=request.user
            )
            inventory.save()
            
            # Добавляем имущество в инвентаризацию
            assets_query = Asset.objects.filter(is_written_off=False)
            
            # Если пользователь не админ и у него есть подразделение - фильтруем по подразделению
            if not (request.user.is_staff or request.user.is_superuser) and department:
                assets_query = assets_query.filter(department=department)
            
            for asset in assets_query:
                InventoryItem.objects.create(
                    inventory=inventory,
                    asset=asset,
                    total_quantity=asset.quantity,
                    scanned_quantity=0
                )
            
            messages.success(request, f'Плановая инвентаризация успешно начата.')
            return redirect('current_inventory')
    
    return render(request, 'inventory/planned_inventory.html')


@login_required
def unplanned_inventory(request):
    """Внеплановая инвентаризация"""
    # Проверяем, есть ли активная инвентаризация
    has_active = check_active_inventory(request)
    if has_active:
        messages.warning(request, 'Невозможно начать новую инвентаризацию, пока не завершена текущая.')
        return redirect('inventory_home')
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        
        if start_date:
            # Получаем подразделение пользователя
            try:
                user_profile = request.user.profile
                department = user_profile.department
            except:
                user_profile = None
                department = None
            
            # Создаем новую инвентаризацию
            inventory = Inventory(
                name=f'Внеплановая инвентаризация от {start_date}',
                start_date=start_date,
                inventory_type='unplanned',
                status='active',
                department=department,
                created_by=request.user
            )
            inventory.save()
            
            # Добавляем имущество в инвентаризацию
            assets_query = Asset.objects.filter(is_written_off=False)
            
            # Если пользователь не админ и у него есть подразделение - фильтруем по подразделению
            if not (request.user.is_staff or request.user.is_superuser) and department:
                assets_query = assets_query.filter(department=department)
            
            for asset in assets_query:
                InventoryItem.objects.create(
                    inventory=inventory,
                    asset=asset,
                    total_quantity=asset.quantity,
                    scanned_quantity=0
                )
            
            messages.success(request, f'Внеплановая инвентаризация успешно начата.')
            return redirect('current_inventory')
    
    return render(request, 'inventory/unplanned_inventory.html')


@login_required
def current_inventory(request):
    """Текущая инвентаризация"""
    try:
        # Проверяем, является ли пользователь администратором
        is_admin = request.user.is_staff or request.user.is_superuser
        
        # Получаем подразделение пользователя
        try:
            user_profile = request.user.profile
            department = user_profile.department
        except:
            user_profile = None
            department = None
        
        # Получаем активную инвентаризацию
        inventory_query = Inventory.objects.filter(status='active')
        
        # Если пользователь не админ и у него есть подразделение - фильтруем по подразделению
        if not is_admin and department:
            inventory_query = inventory_query.filter(department=department)
        
        # Если нет активных инвентаризаций
        if not inventory_query.exists():
            messages.warning(request, 'Нет активных инвентаризаций.')
            return redirect('inventory_home')
        
        # Берем первую активную инвентаризацию
        inventory = inventory_query.first()
        
        # Получаем элементы инвентаризации
        inventory_items = InventoryItem.objects.filter(inventory=inventory).select_related('asset')
        
        # Если пользователь не админ и у него есть подразделение - дополнительно фильтруем имущество по подразделению
        if not is_admin and department:
            inventory_items = inventory_items.filter(asset__department=department)
        
        # Преобразуем данные для удобного использования в шаблоне
        items = []
        for item in inventory_items:
            items.append({
                'id': item.id,
                'inventory_number': item.asset.inventory_number,
                'asset_name': item.asset.asset_name,
                'total_quantity': item.total_quantity,
                'scanned_quantity': item.scanned_quantity,
                'status': 'scanned' if item.scanned_quantity > 0 else 'not-scanned',
                'location_name': item.asset.get_location_name() or 'Не указано',
                'department_name': item.asset.department.name if item.asset.department else 'Не указано',
            })
        
        return render(request, 'inventory/current_inventory.html', {
            'inventory': inventory,
            'items': items
        })
    except Inventory.DoesNotExist:
        messages.warning(request, 'Нет активных инвентаризаций.')
        return redirect('inventory_home')


@login_required
@department_access_required
def scan_asset(request):
    """Сканирование QR-кода имущества"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        inventory_id = request.POST.get('inventory_id')
        qr_code = request.POST.get('qr_code')
        
        try:
            inventory = Inventory.objects.get(id=inventory_id, status='active')
            
            # Проверяем доступ к инвентаризации
            if not (request.user.is_staff or request.user.is_superuser):
                try:
                    user_profile = request.user.profile
                    user_department = user_profile.department
                    
                    if not user_department or (inventory.department and inventory.department != user_department):
                        return JsonResponse({
                            'success': False,
                            'message': 'У вас нет доступа к этой инвентаризации.'
                        })
                except:
                    return JsonResponse({
                        'success': False,
                        'message': 'У вас нет доступа к этой инвентаризации.'
                    })
            
            asset = Asset.objects.get(qr_code=qr_code, is_written_off=False)
            
            inventory_item = InventoryItem.objects.get(inventory=inventory, asset=asset)
            
            if inventory_item.scan_asset():
                return JsonResponse({
                    'success': True,
                    'message': f'Имущество "{asset.asset_name}" успешно отсканировано.',
                    'item_id': inventory_item.id,
                    'scanned_quantity': inventory_item.scanned_quantity,
                    'total_quantity': inventory_item.total_quantity
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Имущество "{asset.asset_name}" уже полностью учтено.'
                })
        
        except Inventory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Инвентаризация не найдена или не активна.'
            })
        except Asset.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Имущество с таким QR-кодом не найдено или списано.'
            })
        except InventoryItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Данное имущество не включено в текущую инвентаризацию.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при сканировании: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Неверный запрос.'
    })


@login_required
@department_access_required
def complete_inventory(request, pk):
    """Завершение инвентаризации"""
    inventory = get_object_or_404(Inventory, pk=pk)
    
    if request.method == 'POST':
        inventory.complete_inventory()
        messages.success(request, 'Инвентаризация успешно завершена.')
        return redirect('inventory_history')
    
    return render(request, 'inventory/complete_inventory.html', {'inventory': inventory})


@login_required
@department_access_required
def inventory_history(request):
    """История инвентаризаций"""
    # Проверяем, является ли пользователь администратором
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Получаем подразделение пользователя
    try:
        user_profile = request.user.profile
        department = user_profile.department
    except:
        user_profile = None
        department = None
    
    # Получаем завершенные инвентаризации
    history_query = Inventory.objects.filter(status='completed')
    
    # Если пользователь не админ и у него есть подразделение - фильтруем по подразделению
    if not is_admin and department:
        history_query = history_query.filter(department=department)
    
    return render(request, 'inventory/inventory_history.html', {
        'history': history_query
    })


@login_required
@department_access_required
def inventory_detail(request, pk):
    """Детальная информация об инвентаризации"""
    inventory = get_object_or_404(Inventory, pk=pk)
    
    # Проверяем, является ли пользователь администратором
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Получаем подразделение пользователя
    try:
        user_profile = request.user.profile
        department = user_profile.department
    except:
        user_profile = None
        department = None
    
    # Запрашиваем все элементы инвентаризации
    inventory_items = InventoryItem.objects.filter(inventory=inventory).select_related('asset')
    
    # Если пользователь не админ и у него есть подразделение - фильтруем имущество по подразделению
    if not is_admin and department:
        inventory_items = inventory_items.filter(asset__department=department)
    
    items = []
    for item in inventory_items:
        items.append({
            'id': item.id,
            'inventory_number': item.asset.inventory_number,
            'asset_name': item.asset.asset_name,
            'total_quantity': item.total_quantity,
            'scanned_quantity': item.scanned_quantity,
            'location_name': item.asset.get_location_name() or 'Не указано',
            'department_name': item.asset.department.name if item.asset.department else 'Не указано',
        })
    
    return render(request, 'inventory/inventory_detail.html', {
        'inventory': inventory,
        'items': items
    })


# @login_required
# def generate_inv1(request, pk, format_type=None):
#     """Генерация формы ИНВ-1"""
#     inventory = get_object_or_404(Inventory, pk=pk)
#     inventory_items = InventoryItem.objects.filter(inventory=inventory)
    
#     context = {
#         'inventory': inventory,
#         'items': inventory_items,
#         'start_date': inventory.start_date.strftime('%d.%m.%Y'),
#         'end_date': inventory.date_completed.strftime('%d.%m.%Y') if inventory.date_completed else ''
#     }
    
#     if format_type == 'pdf':
#         # Генерация PDF
#         html_string = render_to_string('inventory/inv1_pdf.html', context)
#         html = HTML(string=html_string)
#         pdf_file = html.write_pdf()
        
#         response = HttpResponse(pdf_file, content_type='application/pdf')
#         response['Content-Disposition'] = f'filename="inv1_{inventory.id}.pdf"'
#         return response
    
#     return render(request, 'inventory/inv1.html', context)


# @login_required
# def generate_inv18(request, pk, format_type=None):
#     inventory = get_object_or_404(Inventory, pk=pk)
#     inventory_items = list(InventoryItem.objects.filter(inventory=inventory))

#     for item in inventory_items:
#         scanned = item.scanned_quantity or 0
#         quantity = item.total_quantity or 0
#         value = item.asset.book_value or 0
#         item.missing_quantity = max(quantity - scanned, 0)
#         item.scanned_value = scanned * value if scanned > 0 else 0

#     first_table_items = inventory_items[:6]
#     second_table_items = inventory_items[6:22]

#     # Считаем итоги для первой таблицы
#     total_scanned_1 = sum(item.scanned_quantity or 0 for item in first_table_items)
#     scanned_value_1 = sum(item.scanned_value for item in first_table_items)
#     total_quantity_1 = sum(item.total_quantity or 0 for item in first_table_items)
#     missing_value_1 = sum(item.missing_quantity * (item.asset.book_value or 0) for item in first_table_items)
#     missing_count_1 = total_quantity_1 - total_scanned_1

#     # Аналогично для второй таблицы
#     total_scanned_2 = sum(item.scanned_quantity or 0 for item in second_table_items)
#     scanned_value_2 = sum(item.scanned_value for item in second_table_items)
#     total_quantity_2 = sum(item.total_quantity or 0 for item in second_table_items)
#     missing_value_2 = sum(item.missing_quantity * (item.asset.book_value or 0) for item in second_table_items)
#     missing_count_2 = total_quantity_2 - total_scanned_2

#     context = {
#         'inventory': inventory,
#         'items': inventory_items,
#         'first_table_items': first_table_items,
#         'second_table_items': second_table_items,
#         'start_date': inventory.start_date.strftime('%d.%m.%Y'),
#         'end_date': inventory.date_completed.strftime('%d.%m.%Y') if inventory.date_completed else '',
#         'total_scanned_1': total_scanned_1,
#         'scanned_value_1': scanned_value_1,
#         'missing_value_1': missing_value_1,
#         'missing_count_1': missing_count_1,
#         'total_scanned_2': total_scanned_2,
#         'scanned_value_2': scanned_value_2,
#         'missing_value_2': missing_value_2,
#         'missing_count_2': missing_count_2,
#     }

#     if format_type == 'pdf':
#         html_string = render_to_string('inventory/inv18_pdf.html', context)
#         html = HTML(string=html_string)
#         pdf_file = html.write_pdf()

#         response = HttpResponse(pdf_file, content_type='application/pdf')
#         response['Content-Disposition'] = f'filename="inv18_{inventory.id}.pdf"'
#         return response

#     return render(request, 'inventory/inv18.html', context)


login_required
def generate_inv1(request, pk, format_type=None):
    inventory = get_object_or_404(Inventory, pk=pk)
    inventory_items = list(InventoryItem.objects.filter(inventory=inventory))

    for item in inventory_items:
        scanned = item.scanned_quantity or 0
        quantity = item.total_quantity or 0
        value = item.asset.book_value or 0
        item.missing_quantity = max(quantity - scanned, 0)
        item.scanned_value = scanned * value if scanned > 0 else 0

    first_table_items = inventory_items[:6]
    second_table_items = inventory_items[6:22]

    context = {
        'inventory': inventory,
        'items': inventory_items,
        'first_table_items': first_table_items,
        'second_table_items': second_table_items,
        'start_date': inventory.start_date.strftime('%d.%m.%Y'),
        'end_date': inventory.date_completed.strftime('%d.%m.%Y') if inventory.date_completed else '',
        'total_scanned_1': sum(item.scanned_quantity or 0 for item in first_table_items),
        'scanned_value_1': sum(item.scanned_value for item in first_table_items),
        'missing_value_1': sum(item.missing_quantity * (item.asset.book_value or 0) for item in first_table_items),
        'missing_count_1': sum(item.total_quantity or 0 for item in first_table_items) - sum(item.scanned_quantity or 0 for item in first_table_items),
        'total_scanned_2': sum(item.scanned_quantity or 0 for item in second_table_items),
        'scanned_value_2': sum(item.scanned_value for item in second_table_items),
        'missing_value_2': sum(item.missing_quantity * (item.asset.book_value or 0) for item in second_table_items),
        'missing_count_2': sum(item.total_quantity or 0 for item in second_table_items) - sum(item.scanned_quantity or 0 for item in second_table_items),
    }

    if format_type == 'pdf':
        html_string = render_to_string('inventory/inv1_pdf.html', context)
        temp_html = os.path.join(settings.MEDIA_ROOT, f'inv1_{pk}.html')
        temp_png = os.path.join(settings.MEDIA_ROOT, f'inv1_{pk}.png')
        temp_pdf = os.path.join(settings.MEDIA_ROOT, f'inv1_{pk}.pdf')

        # Сохраняем HTML временно
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(html_string)

        # Настраиваем headless Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1200x800')

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f'file://{temp_html}')
        S = lambda X: driver.execute_script('return document.body.parentNode.scroll' + X)
        driver.set_window_size(S('Width'), S('Height'))  # Автоматическая подгонка окна
        driver.save_screenshot(temp_png)
        driver.quit()

        # Преобразуем PNG в PDF
        image = Image.open(temp_png).convert('RGB')
        pdf = FPDF()
        pdf.add_page()
        pdf.image(temp_png, x=0, y=0, w=210)  # ширина A4 = 210 мм
        pdf.output(temp_pdf)

        with open(temp_pdf, 'rb') as f:
            pdf_data = f.read()

        # Очистка временных файлов
        os.remove(temp_html)
        os.remove(temp_png)
        os.remove(temp_pdf)

        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="inv1_{pk}.pdf"'
        return response

    return render(request, 'inventory/inv1.html', context)

def check_active_inventory(request):
    """Проверяет наличие активных инвентаризаций доступных пользователю"""
    is_admin = request.user.is_staff or request.user.is_superuser
    
    try:
        user_profile = request.user.profile
        department = user_profile.department
    except:
        user_profile = None
        department = None
    
    inventory_query = Inventory.objects.filter(status='active')
    
    # Если пользователь не админ и у него есть подразделение - фильтруем по подразделению
    if not is_admin and department:
        inventory_query = inventory_query.filter(department=department)
    
    return inventory_query.exists()


@login_required
def generate_inv18(request, pk, format_type=None):
    inventory = get_object_or_404(Inventory, pk=pk)
    inventory_items = list(InventoryItem.objects.filter(inventory=inventory))

    for item in inventory_items:
        scanned = item.scanned_quantity or 0
        quantity = item.total_quantity or 0
        value = item.asset.book_value or 0
        item.missing_quantity = max(quantity - scanned, 0)
        item.scanned_value = scanned * value if scanned > 0 else 0

    first_table_items = inventory_items[:6]
    second_table_items = inventory_items[6:22]

    context = {
        'inventory': inventory,
        'items': inventory_items,
        'first_table_items': first_table_items,
        'second_table_items': second_table_items,
        'start_date': inventory.start_date.strftime('%d.%m.%Y'),
        'end_date': inventory.date_completed.strftime('%d.%m.%Y') if inventory.date_completed else '',
        'total_scanned_1': sum(item.scanned_quantity or 0 for item in first_table_items),
        'scanned_value_1': sum(item.scanned_value for item in first_table_items),
        'missing_value_1': sum(item.missing_quantity * (item.asset.book_value or 0) for item in first_table_items),
        'missing_count_1': sum(item.total_quantity or 0 for item in first_table_items) - sum(item.scanned_quantity or 0 for item in first_table_items),
        'total_scanned_2': sum(item.scanned_quantity or 0 for item in second_table_items),
        'scanned_value_2': sum(item.scanned_value for item in second_table_items),
        'missing_value_2': sum(item.missing_quantity * (item.asset.book_value or 0) for item in second_table_items),
        'missing_count_2': sum(item.total_quantity or 0 for item in second_table_items) - sum(item.scanned_quantity or 0 for item in second_table_items),
    }

    if format_type == 'pdf':
        html_string = render_to_string('inventory/inv18_pdf.html', context)
        temp_html = os.path.join(settings.MEDIA_ROOT, f'inv18_{pk}.html')
        temp_png = os.path.join(settings.MEDIA_ROOT, f'inv18_{pk}.png')
        temp_pdf = os.path.join(settings.MEDIA_ROOT, f'inv18_{pk}.pdf')

        # Сохраняем HTML временно
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(html_string)

        # Настраиваем headless Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1200x800')

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f'file://{temp_html}')
        S = lambda X: driver.execute_script('return document.body.parentNode.scroll' + X)
        driver.set_window_size(S('Width'), S('Height'))  # Автоматическая подгонка окна
        driver.save_screenshot(temp_png)
        driver.quit()

        # Преобразуем PNG в PDF
        image = Image.open(temp_png).convert('RGB')
        pdf = FPDF()
        pdf.add_page()
        pdf.image(temp_png, x=0, y=0, w=210)  # ширина A4 = 210 мм
        pdf.output(temp_pdf)

        with open(temp_pdf, 'rb') as f:
            pdf_data = f.read()

        # Очистка временных файлов
        os.remove(temp_html)
        os.remove(temp_png)
        os.remove(temp_pdf)

        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="inv18_{pk}.pdf"'
        return response

    return render(request, 'inventory/inv18.html', context)

def check_active_inventory(request):
    """Проверяет наличие активных инвентаризаций доступных пользователю"""
    is_admin = request.user.is_staff or request.user.is_superuser
    
    try:
        user_profile = request.user.profile
        department = user_profile.department
    except:
        user_profile = None
        department = None
    
    inventory_query = Inventory.objects.filter(status='active')
    
    # Если пользователь не админ и у него есть подразделение - фильтруем по подразделению
    if not is_admin and department:
        inventory_query = inventory_query.filter(department=department)
    
    return inventory_query.exists()


# Управление пользователями и подразделениями

@staff_member_required
def department_list(request):
    """Список структурных подразделений"""
    departments = Department.objects.all()
    return render(request, 'inventory/department_list.html', {
        'departments': departments
    })


@staff_member_required
def department_create(request):
    """Создание структурного подразделения"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Структурное подразделение "{department.name}" успешно создано.')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    
    return render(request, 'inventory/department_form.html', {
        'form': form,
        'title': 'Создание структурного подразделения'
    })


@staff_member_required
def department_update(request, pk):
    """Редактирование структурного подразделения"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Структурное подразделение "{department.name}" успешно обновлено.')
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    
    return render(request, 'inventory/department_form.html', {
        'form': form,
        'department': department,
        'title': 'Редактирование структурного подразделения'
    })


@staff_member_required
def department_delete(request, pk):
    """Удаление структурного подразделения"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        name = department.name
        department.delete()
        messages.success(request, f'Структурное подразделение "{name}" успешно удалено.')
        return redirect('department_list')
    
    return render(request, 'inventory/department_confirm_delete.html', {
        'department': department
    })


@staff_member_required
def user_list(request):
    """Список пользователей"""
    users = User.objects.all().order_by('last_name')
    return render(request, 'inventory/user_list.html', {
        'users': users
    })


@staff_member_required
def user_create(request):
    """Создание пользователя (только для администраторов)"""
    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Пользователь "{user.username}" успешно создан.')
            return redirect('user_list')
    else:
        form = UserEditForm()
    
    return render(request, 'inventory/user_form.html', {
        'form': form,
        'title': 'Создание нового пользователя'
    })


@staff_member_required
def user_detail(request, pk):
    """Информация о пользователе"""
    user = get_object_or_404(User, pk=pk)
    return render(request, 'inventory/user_detail.html', {
        'user_obj': user  # Используем user_obj чтобы избежать конфликта имен
    })


@staff_member_required
def user_update(request, pk):
    """Редактирование пользователя (только для администраторов)"""
    user = get_object_or_404(User, pk=pk)
    
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        # Создаем профиль, если его нет
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        # Используем расширенную форму с полями для профиля
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Информация о пользователе "{user.username}" успешно обновлена.')
            return redirect('user_list')
    else:
        # Заполняем форму данными пользователя и его профиля
        form = UserEditForm(instance=user)
    
    return render(request, 'inventory/user_form.html', {
        'form': form,
        'user_obj': user,
        'title': 'Редактирование пользователя'
    })


@staff_member_required
def user_delete(request, pk):
    """Удаление пользователя (только для администраторов)"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Пользователь "{username}" успешно удален.')
        return redirect('user_list')
    
    return render(request, 'inventory/user_confirm_delete.html', {
        'user_obj': user
    })













@login_required
@staff_member_required
def admin_departments_inventory(request):
    """Просмотр текущих инвентаризаций всех подразделений для администратора"""
    # Получаем список всех активных инвентаризаций
    active_inventories = Inventory.objects.filter(status='active')
    
    # Предварительная загрузка подразделений и создателей для оптимизации запросов
    active_inventories = active_inventories.select_related('department', 'created_by')
    
    # Формируем словарь со статистикой по каждой инвентаризации
    inventories_data = []
    for inventory in active_inventories:
        # Подсчитываем количество элементов и проверенных элементов
        items_count = InventoryItem.objects.filter(inventory=inventory).count()
        scanned_count = InventoryItem.objects.filter(
            inventory=inventory, 
            scanned_quantity__gt=0
        ).count()
        
        # Вычисляем процент выполнения
        progress = 0
        if items_count > 0:
            progress = round((scanned_count / items_count) * 100)
        
        # Формируем данные для отображения
        inventories_data.append({
            'id': inventory.id,
            'name': inventory.name,
            'department': inventory.department.name if inventory.department else 'Не указано',
            'created_by': inventory.created_by.get_full_name() or inventory.created_by.username,
            'start_date': inventory.start_date,
            'items_count': items_count,
            'scanned_count': scanned_count,
            'progress': progress
        })
    
    return render(request, 'inventory/admin_departments_inventory.html', {
        'inventories': inventories_data
    })


@login_required
def update_status(request):
    """
    AJAX endpoint для обновления статуса имущества в инвентаризации
    """
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        item_id = data.get('item_id')
        status = data.get('status')
        quantity = data.get('quantity', 0)
        
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            quantity = 0
            
        # Проверяем активную инвентаризацию
        active_inventory = Inventory.objects.filter(status='active').first()
        if not active_inventory:
            return JsonResponse({
                'success': False,
                'message': 'Нет активной инвентаризации'
            })
            
        try:
            # Получаем элемент инвентаризации
            inventory_item = InventoryItem.objects.get(id=item_id, inventory=active_inventory)
            
            # Обновляем количество и последнюю дату сканирования
            inventory_item.scanned_quantity = quantity
            inventory_item.last_scan_date = timezone.now()
            inventory_item.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Статус обновлен: {inventory_item.asset.asset_name}",
                'item_id': inventory_item.id
            })
            
        except InventoryItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Элемент инвентаризации не найден'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Метод не поддерживается'}) 