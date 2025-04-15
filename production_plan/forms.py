from django import forms
from .models import ProductionPlan


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class ProductionPlanForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = ProductionPlan
        fields = ['customer', 'order', 'product', 'quantity', 'plan', 'progress', 'deadline']
