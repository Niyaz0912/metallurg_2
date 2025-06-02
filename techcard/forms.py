from django import forms
from .models import TechCard, TechCardStage


class TechCardForm(forms.ModelForm):
    class Meta:
        model = TechCard
        fields = ['production_plan', 'drawing', 'steel_grade', 'total_quantity', 'technological_process']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Добавляем класс Bootstrap ко всем полям кроме FileField (для которых можно добавить свой класс)
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control-file'})


class TechCardStageForm(forms.ModelForm):
    class Meta:
        model = TechCardStage
        fields = ['name', 'equipment', 'operation_time', 'instructions', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
