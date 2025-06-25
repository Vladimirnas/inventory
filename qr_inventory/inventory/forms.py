from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Inventory, Department
from assets.models import Asset
from datetime import date
from accounts.models import UserProfile


class PlannedInventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d')
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d')
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'Дата окончания не может быть раньше даты начала')
        
        return cleaned_data


class UnplannedInventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d')
            }),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.inventory_type = 'unplanned'
        
        if commit:
            instance.save()
        
        return instance


class CompleteInventoryForm(forms.Form):
    inventory_id = forms.IntegerField(widget=forms.HiddenInput())
    confirm = forms.BooleanField(
        label='Подтверждаю завершение инвентаризации',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class UserEditForm(forms.ModelForm):
    username = forms.CharField(label='Логин', required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='Имя', required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Фамилия', required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    middle_name = forms.CharField(label='Отчество', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    name_position = forms.CharField(
        label='Должность',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    department = forms.ModelChoiceField(
        label='Структурное подразделение',
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label='Телефон',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
            'is_active': 'Активен',
            'is_staff': 'Сотрудник',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.profile
                self.fields['middle_name'].initial = profile.middle_name
                self.fields['name_position'].initial = profile.name_position
                self.fields['department'].initial = profile.department
                self.fields['phone'].initial = profile.phone
            except UserProfile.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.middle_name = self.cleaned_data.get('middle_name')
            profile.name_position = self.cleaned_data.get('name_position')
            profile.department = self.cleaned_data.get('department')
            profile.phone = self.cleaned_data.get('phone')
            profile.save()
        
        return user


# УДАЛЯЕМ: PositionForm и импорт Position
# from .models import Position — удалить
# class PositionForm — удалить
