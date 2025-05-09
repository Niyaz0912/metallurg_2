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
        fields = ['customer', 'order', 'product', 'quantity', 'deadline']  # и другие поля

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if not deadline:
            raise forms.ValidationError("Это поле обязательно")
        return deadline


