from django import forms
from .models import ProductionPlan, Supply


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class ProductionPlanForm(StyleFormMixin, forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label='Срок отгрузки'
    )

    class Meta:
        model = ProductionPlan
        fields = ['customer', 'order', 'product', 'quantity', 'plan', 'progress', 'deadline']


class SupplyForm(StyleFormMixin, forms.ModelForm):
    expected_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Ожидаемая дата поставки'
    )
    received_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Дата получения'
    )

    class Meta:
        model = Supply
        fields = ['name', 'quantity', 'expected_date', 'received_date', 'status']
