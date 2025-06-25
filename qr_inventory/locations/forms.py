from django import forms
from .models import Location
from assets.models import Asset


class LocationForm(forms.ModelForm):
    """Форма для создания и редактирования помещения"""
    class Meta:
        model = Location
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название помещения'})
        }


class AssignEquipmentForm(forms.Form):
    """Форма для назначения оборудования в помещение"""
    location_id = forms.IntegerField(widget=forms.HiddenInput())
    inventory_number = forms.CharField(
        label='Инвентарный номер',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите инвентарный номер оборудования'
        })
    )
    
    def clean_inventory_number(self):
        inventory_number = self.cleaned_data.get('inventory_number')
        
        # Проверяем существование оборудования с таким инвентарным номером
        try:
            asset = Asset.objects.get(inventory_number=inventory_number, is_written_off=False)
        except Asset.DoesNotExist:
            raise forms.ValidationError('Оборудование с указанным инвентарным номером не найдено или списано')
            
        return inventory_number 