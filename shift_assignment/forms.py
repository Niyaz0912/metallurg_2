from django import forms
from django.contrib.auth import get_user_model
from .models import ShiftAssignment
from django.utils.translation import gettext as _

User = get_user_model()


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        css_class = kwargs.pop('css_class', 'form-control')
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing_classes} {css_class}".strip()


class ShiftAssignmentForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = [
            'production_plan',
            'shift_date',
            'shift_type',
            'machine_number',
            'operator',
            'planned_quantity',
            'order_name',
            'work_type',
            'drawing',
            'notes',
        ]
        widgets = {
            'shift_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class UpdateShiftAssignmentForm(StyleFormMixin, forms.ModelForm):
    actual_quantity = forms.IntegerField(
        min_value=0,
        required=True,
        label='Фактическое количество',
        help_text='Введите фактическое количество (неотрицательное число)'
    )

    class Meta:
        model = ShiftAssignment
        fields = [
            'actual_quantity',
            'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_actual_quantity(self):
        qty = self.cleaned_data.get('actual_quantity')
        if qty is None or qty < 0:
            raise forms.ValidationError("Количество не может быть отрицательным")
        return qty


class EditShiftAssignmentForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = [
            'production_plan',
            'shift_date',
            'shift_type',
            'machine_number',
            'operator',
            'order_name',
            'work_type',
            'planned_quantity',
            'drawing',
            'notes',
        ]
        widgets = {
            'shift_date': forms.DateInput(attrs={'type': 'date'}),
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
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if not file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError(
                    _('Поддерживаются только файлы Excel (.xlsx, .xls)')
                )
            # Можно добавить проверку размера файла, например:
            # if file.size > 5 * 1024 * 1024:
            #     raise forms.ValidationError(_('Размер файла не должен превышать 5 МБ'))
        return file


class CompleteAssignmentForm(forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ['actual_quantity', 'notes']
        labels = {
            'actual_quantity': 'Фактическое количество',
            'notes': 'Комментарии'
        }
        widgets = {
            'actual_quantity': forms.NumberInput(attrs={'min': 0}),
        }