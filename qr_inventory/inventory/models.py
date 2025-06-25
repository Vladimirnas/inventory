from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from assets.models import Asset


class Inventory(models.Model):
    """Модель инвентаризации"""
    TYPE_CHOICES = (
        ('planned', 'Плановая'),
        ('unplanned', 'Внеплановая'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Активная'),
        ('completed', 'Завершена'),
    )
    
    name = models.CharField('Название', max_length=255)
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    inventory_type = models.CharField('Тип инвентаризации', max_length=10, choices=TYPE_CHOICES, default='unplanned')
    status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='active')
    date_completed = models.DateTimeField('Дата завершения', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        related_name='inventories',
        verbose_name='Структурное подразделение',
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_inventories',
        verbose_name='Создатель',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Инвентаризация'
        verbose_name_plural = 'Инвентаризации'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_inventory_type_display()}) - {self.get_status_display()}"
    
    def complete_inventory(self):
        """Завершить инвентаризацию"""
        self.status = 'completed'
        self.date_completed = timezone.now()
        self.save()
        
        # Не меняем статус непросканированных элементов
        # Обновляем только дату завершения инвентаризации
    
    @property
    def items_count(self):
        """Возвращает количество элементов инвентаризации"""
        return self.inventory_items.count()


class InventoryItem(models.Model):
    """Модель элемента инвентаризации"""
    STATUS_CHOICES = (
        ('pending', 'Ожидает проверки'),
        ('completed', 'Проверено'),
    )
    
    inventory = models.ForeignKey(
        Inventory, 
        on_delete=models.CASCADE, 
        related_name='inventory_items',
        verbose_name='Инвентаризация'
    )
    asset = models.ForeignKey(
        Asset, 
        on_delete=models.CASCADE, 
        related_name='inventory_records',
        verbose_name='Имущество'
    )
    total_quantity = models.IntegerField('Общее количество', default=0)
    scanned_quantity = models.IntegerField('Отсканировано', default=0)
    inventory_status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='pending')
    last_scanned = models.DateTimeField('Последнее сканирование', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Элемент инвентаризации'
        verbose_name_plural = 'Элементы инвентаризации'
        unique_together = ('inventory', 'asset')
    
    def __str__(self):
        return f"{self.asset.inventory_number} - {self.scanned_quantity}/{self.total_quantity}"
    
    def scan_asset(self):
        """Отметить имущество как отсканированное"""
        if self.scanned_quantity < self.total_quantity:
            self.scanned_quantity += 1
            self.last_scanned = timezone.now()
            if self.scanned_quantity >= self.total_quantity:
                self.inventory_status = 'completed'
            self.save()
            return True
        return False


class Department(models.Model):
    """Модель структурного подразделения"""
    name = models.CharField('Название', max_length=255)
    code = models.CharField('Код', max_length=50, blank=True, null=True)
    description = models.TextField('Описание', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Структурное подразделение'
        verbose_name_plural = 'Структурные подразделения'
        ordering = ['name']
    
    def __str__(self):
        return self.name 


