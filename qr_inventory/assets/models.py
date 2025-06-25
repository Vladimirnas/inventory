from django.db import models
from django.utils import timezone
from locations.models import Location


class Asset(models.Model):
    """Модель имущества/оборудования"""
    inventory_number = models.CharField('Инвентарный номер', max_length=100, unique=True)
    asset_name = models.CharField('Наименование', max_length=255)
    quantity = models.IntegerField('Количество', default=1)
    book_value = models.DecimalField('Балансовая стоимость', max_digits=12, decimal_places=2, null=True, blank=True)
    responsible = models.CharField('Ответственный', max_length=255, null=True, blank=True)
    location = models.ForeignKey(
        Location, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assets', 
        verbose_name='Помещение'
    )
    department = models.ForeignKey(
        'inventory.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        verbose_name='Структурное подразделение'
    )
    year_of_manufacture = models.IntegerField('Год выпуска', null=True, blank=True)
    photo = models.ImageField('Фото', upload_to='assets/', null=True, blank=True)
    qr_code = models.CharField('QR код', max_length=150, null=True, blank=True)
    qr_image = models.ImageField('QR изображение', upload_to='qr_codes/assets/', null=True, blank=True)
    total_written_off = models.PositiveIntegerField(default=0) 
    is_written_off = models.BooleanField('Списано', default=False)
    write_off_date = models.DateTimeField('Дата списания', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Имущество'
        verbose_name_plural = 'Имущество'
        ordering = ['inventory_number']

    def __str__(self):
        return f"{self.inventory_number} - {self.asset_name}"


    def write_off_quantity(self, qty):
        if qty > self.quantity:
            raise ValueError("Нельзя списать больше, чем есть в наличии")

        self.quantity -= qty
        self.total_written_off += qty
        self.last_write_off_date = timezone.now()

        if self.quantity == 0:
            self.is_written_off = True

        self.save()

    def write_off(self):
        """Списание имущества"""
        # written_off = WrittenOffAsset(
        #     inventory_number=self.inventory_number,
        #     asset_name=self.asset_name,
        #     quantity=self.quantity,
        #     book_value=self.book_value,
        #     responsible=self.responsible,
        #     location_name=self.get_location_name(),
        #     department_name=self.department.name if self.department else None,
        #     year_of_manufacture=self.year_of_manufacture,
        #     photo_link=self.photo.name if self.photo else None,
        # )
        # written_off.save()
        
        self.is_written_off = True
        self.write_off_date = timezone.now()
        self.save()
        # return written_off


    

    


    def get_location_name(self):
        """Возвращает название помещения"""
        return self.location.name if self.location else "Не указано"


# class WrittenOffAsset(models.Model):
#     """Модель для хранения истории списанного имущества"""
#     inventory_number = models.CharField('Инвентарный номер', max_length=100)
#     asset_name = models.CharField('Наименование', max_length=255)
#     quantity = models.IntegerField('Количество', default=1)
#     book_value = models.DecimalField('Балансовая стоимость', max_digits=12, decimal_places=2, null=True, blank=True)
#     responsible = models.CharField('Ответственный', max_length=255, null=True, blank=True)
#     location_name = models.CharField('Помещение', max_length=255, null=True, blank=True)
#     department_name = models.CharField('Структурное подразделение', max_length=255, null=True, blank=True)
#     year_of_manufacture = models.IntegerField('Год выпуска', null=True, blank=True)
#     photo_link = models.CharField('Ссылка на фото', max_length=255, null=True, blank=True)
#     write_off_date = models.DateTimeField('Дата списания', default=timezone.now)

#     class Meta:
#         verbose_name = 'Списанное имущество'
#         verbose_name_plural = 'Списанное имущество'
#         ordering = ['-write_off_date']

#     def __str__(self):
#         return f"{self.inventory_number} - {self.asset_name} (списано {self.write_off_date.strftime('%d.%m.%Y')})" 