from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import Http404

from .models import Inventory


def department_access_required(view_func):
    """
    Декоратор, который проверяет доступ пользователя к инвентаризации.
    Администраторы имеют доступ ко всем инвентаризациям.
    Обычные пользователи имеют доступ только к инвентаризациям своего подразделения.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Администраторы имеют доступ ко всем инвентаризациям
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        inventory_id = kwargs.get('pk')
        
        # Пытаемся получить подразделение пользователя
        try:
            user_profile = request.user.profile
            user_department = user_profile.department
            
            # Если пользователь не привязан к подразделению
            if not user_department:
                messages.error(request, 'Вы не привязаны к подразделению. Обратитесь к администратору.')
                return redirect('inventory_home')
                
        except:
            messages.error(request, 'Ошибка при получении данных профиля. Обратитесь к администратору.')
            return redirect('inventory_home')
        
        # Если передан inventory_id, проверяем доступ к конкретной инвентаризации
        if inventory_id:
            try:
                inventory = Inventory.objects.get(pk=inventory_id)
                
                # Если у инвентаризации указано подразделение и оно не совпадает с подразделением пользователя
                if inventory.department and inventory.department != user_department:
                    messages.error(request, 'У вас нет доступа к этой инвентаризации.')
                    return redirect('inventory_home')
                    
            except Inventory.DoesNotExist:
                raise Http404("Инвентаризация не найдена")
        
        # Если все проверки пройдены, вызываем оригинальное представление
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view 