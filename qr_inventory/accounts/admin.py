from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    middle_name = forms.CharField(label='Отчество', max_length=150, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'middle_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        middle_name = self.cleaned_data.get('middle_name')

        if commit:
            user.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.middle_name = middle_name
            profile.save()

        return user


class CustomUserChangeForm(UserChangeForm):
    middle_name = forms.CharField(label='Отчество', max_length=150, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'middle_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['middle_name'].initial = self.instance.profile.middle_name

    def save(self, commit=True):
        user = super().save(commit=False)
        middle_name = self.cleaned_data.get('middle_name')

        if commit:
            user.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.middle_name = middle_name
            profile.save()

        return user


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль пользователя'
    fieldsets = (
        ('Рабочая информация', {
            'fields': ('department', 'name_position')  # заменили position → name_position
        }),
        ('Контактная информация', {
            'fields': ('phone',)
        }),
    )


class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_middle_name', 'get_position', 'get_department')
    list_filter = ('is_staff', 'is_superuser', 'profile__department')  # удалили profile__position
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__middle_name')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'middle_name', 'email')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'middle_name', 'email'),
        }),
    )

    def get_middle_name(self, obj):
        try:
            return obj.profile.middle_name
        except UserProfile.DoesNotExist:
            return '-'
    get_middle_name.short_description = 'Отчество'

    def get_position(self, obj):
        try:
            return obj.profile.name_position  # было: obj.profile.position
        except UserProfile.DoesNotExist:
            return '-'
    get_position.short_description = 'Должность'

    def get_department(self, obj):
        try:
            return obj.profile.department
        except UserProfile.DoesNotExist:
            return '-'
    get_department.short_description = 'Подразделение'


# Замена стандартной админки для User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
