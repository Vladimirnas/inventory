from django.db import models
import uuid
import os
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
from django.urls import reverse


class Location(models.Model):
    """Модель помещения/местонахождения"""
    name = models.CharField('Название помещения', max_length=255)
    qr_code = models.CharField('QR код', max_length=150, unique=True)
    qr_image = models.ImageField('QR изображение', upload_to='qr_codes/locations/', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Помещение'
        verbose_name_plural = 'Помещения'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Если QR код еще не сгенерирован, создаем его
        if not self.qr_code:
            self.qr_code = str(uuid.uuid4())[:8].upper()
        
        # Генерируем QR изображение
        if not self.qr_image:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.qr_code)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            
            # Создаем имя файла
            filename = f'location_{self.qr_code}.png'
            
            # Сохраняем QR изображение
            self.qr_image.save(filename, File(buffer), save=False)
        
        super().save(*args, **kwargs)

    def equipment_count(self):
        """Возвращает количество оборудования в помещении"""
        return self.assets.filter(is_written_off=False).count()
        
    def get_active_equipment(self):
        """Возвращает список активного оборудования в помещении"""
        return self.assets.filter(is_written_off=False)
        
    def get_absolute_url(self):
        """Возвращает URL для просмотра деталей помещения"""
        return reverse('location_detail', args=[str(self.id)])
        
    def get_qr_image_url(self):
        """Возвращает URL к QR-изображению"""
        if self.qr_image:
            return self.qr_image.url
        return None

    def delete(self, *args, **kwargs):
        # Удаляем QR изображение при удалении помещения
        if self.qr_image:
            if os.path.isfile(self.qr_image.path):
                os.remove(self.qr_image.path)
        
        super().delete(*args, **kwargs) 