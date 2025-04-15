from django import forms
from .models import ShiftAssignment
from django.contrib.auth.models import User


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class ShiftAssignmentForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ['customer', 'date', 'machine_number', 'operator', 'order', 'part', 'quantity', 'part_blueprint', 'comment']


class UpdateShiftAssignmentForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ['quantity', 'execution_status', 'comment']

