from django import template

register = template.Library()

@register.filter
def get_range(value):
    """
    Фильтр для создания последовательности чисел от 0 до (value-1)
    Используется как замена функции range() из Python в шаблонах Django
    
    Пример использования в шаблоне:
    {% for i in 5|get_range %}
        {{ i }}  <!-- Выведет 0, 1, 2, 3, 4 -->
    {% endfor %}
    """
    try:
        value = int(value)
        return range(value)
    except (ValueError, TypeError):
        return range(0) 