from django import forms
from .models import Asset
from locations.models import Location
from inventory.models import Department


class LocationWidget(forms.TextInput):
    """Виджет для ввода помещения с возможностью создания нового"""
    def __init__(self, attrs=None):
        default_attrs = {'class': 'form-control', 'placeholder': 'Введите название помещения'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class AssetForm(forms.ModelForm):
    """Форма для создания/редактирования имущества"""
    location_input = forms.CharField(
        label='Помещение', 
        required=False,
        widget=LocationWidget()
    )
    
    class Meta:
        model = Asset
        fields = [
            'inventory_number', 'asset_name', 'quantity', 'book_value', 
            'responsible', 'location', 'department', 'year_of_manufacture', 'photo'
        ]
        widgets = {
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'book_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'responsible': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control d-none'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'year_of_manufacture': forms.NumberInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
    
    def __init__(self, *args, **kwargs):
        is_admin = kwargs.pop('is_admin', False)
        user_department = kwargs.pop('user_department', None)
        super().__init__(*args, **kwargs)
        
        # Если есть экземпляр с указанным помещением
        if self.instance and self.instance.location:
            self.fields['location_input'].initial = self.instance.location.name
        
        # Ограничиваем доступ к выбору подразделения для неадминистраторов
        if not is_admin and user_department:
            # Делаем поле подразделения доступным только для чтения
            self.fields['department'].disabled = True
            self.fields['department'].widget.attrs['readonly'] = True
            
            # Ограничиваем выбор только подразделением пользователя
            self.fields['department'].queryset = Department.objects.filter(id=user_department.id)
            self.fields['department'].initial = user_department
            
            # Добавляем подсказку
            self.fields['department'].help_text = 'Вы можете добавлять имущество только в свое подразделение'
            
    def clean(self):
        cleaned_data = super().clean()
        location_input = cleaned_data.get('location_input')
        location = cleaned_data.get('location')
        
        # Если пользователь ввел название помещения
        if location_input:
            # Ищем помещение с таким названием или создаем новое
            location, created = Location.objects.get_or_create(name=location_input)
            cleaned_data['location'] = location
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Обновляем помещение если необходимо
        location_input = self.cleaned_data.get('location_input')
        if location_input:
            location, created = Location.objects.get_or_create(name=location_input)
            instance.location = location
        
        if commit:
            instance.save()
        
        return instance


class UploadCSVForm(forms.Form):
    """Форма для загрузки CSV файла"""
    file = forms.FileField(
        label='Выберите CSV файл',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )




class WriteOffAssetForm(forms.Form):
    """Форма для списания имущества с указанием количества"""
    asset_id = forms.IntegerField(widget=forms.HiddenInput())

    quantity = forms.IntegerField(
        label='Количество для списания',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    confirm = forms.BooleanField(
        label='Подтверждаю списание имущества',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        asset_id = self.initial.get('asset_id') or self.data.get('asset_id')
        self.asset = None
        if asset_id:
            try:
                self.asset = Asset.objects.get(id=asset_id, is_written_off=False)
                self.fields['quantity'].widget.attrs['max'] = self.asset.quantity
            except Asset.DoesNotExist:
                pass

    def clean_asset_id(self):
        asset_id = self.cleaned_data.get('asset_id')
        try:
            self.asset = Asset.objects.get(id=asset_id, is_written_off=False)
            return asset_id
        except Asset.DoesNotExist:
            raise forms.ValidationError("Имущество не найдено или уже списано")

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if not self.asset:
            raise forms.ValidationError("Имущество не найдено.")
        if quantity > self.asset.quantity:
            raise forms.ValidationError(f"Максимально можно списать {self.asset.quantity} шт.")
        return quantity


class UpdateResponsibleForm(forms.Form):
    """Форма для обновления ответственного за имущество"""
    asset_id = forms.IntegerField(widget=forms.HiddenInput())
    responsible = forms.CharField(
        label='Ответственный',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    ) 