from django import forms
from django.contrib.auth import get_user_model
from .models import ShiftAssignment
from django.utils.translation import gettext as _


User = get_user_model()


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class ShiftAssignmentForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = [
            'production_plan',
            'shift_date',
            'shift_type',
            'machine_number',  # временное поле вместо machine
            'operator',
            'planned_quantity',
            'status',
            'drawing',
            'notes',
        ]
        widgets = {
            'shift_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class UpdateShiftAssignmentForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = [
            'actual_quantity',
            'status',
            'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label=_('Excel файл'),
        help_text=_('Файл должен содержать все обязательные колонки'),
        widget=forms.FileInput(attrs={
            'accept': '.xlsx, .xls',
            'class': 'form-control-lg'
        }),
        validators=[
            # Можно добавить кастомные валидаторы при необходимости
        ]
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if not file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError(
                    _('Поддерживаются только файлы Excel (.xlsx, .xls)')
                )
            # Дополнительные проверки файла при необходимости
        return file
