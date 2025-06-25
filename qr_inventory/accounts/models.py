from django.db import models
from django.contrib.auth.models import User
from inventory.models import Department  # Position больше не нужен

# Модель расширенного профиля пользователя
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Удалено поле position
    name_position = models.CharField('Должность', max_length=255)  # Переименовал verbose_name
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL,
        related_name='employees',
        verbose_name='Структурное подразделение',
        blank=True, 
        null=True
    )
    phone = models.CharField('Телефон', max_length=20, blank=True, null=True)
    middle_name = models.CharField('Отчество', max_length=150, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f"Профиль {self.user.username}"
        
    @property
    def full_name(self):
        """Полное имя пользователя"""
        if self.middle_name:
            return f"{self.user.last_name} {self.user.first_name} {self.middle_name}"
        return f"{self.user.last_name} {self.user.first_name}"
