from django import forms
from django.contrib.auth import get_user_model
from .models import ShiftAssignment

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
    excel_file = forms.FileField(label='Выберите Excel файл')
