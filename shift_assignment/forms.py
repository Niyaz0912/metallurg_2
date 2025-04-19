from django import forms
from .models import ShiftAssignment, MachineStatus
from django.contrib.auth import get_user_model

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
            'customer',
            'date',
            'machine_number',
            'operator',
            'part_blueprint',
            'execution_status',
            'comment',
            'quantity',
        ]


class UpdateShiftAssignmentForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ['quantity', 'execution_status', 'comment']


class MachineStatusForm(StyleFormMixin, forms.ModelForm):
    breakdown_time = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label='Дата и время поломки'
    )

    class Meta:
        model = MachineStatus
        fields = ['machine_number', 'status', 'breakdown_time', 'notes']

