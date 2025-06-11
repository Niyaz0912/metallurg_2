from django import forms
from .models import TechCard, TechCardStage
from production_plan.models import ProductionPlan


class TechCardForm(forms.ModelForm):
    class Meta:
        model = TechCard
        fields = ['production_plan', 'drawing', 'steel_grade', 'technological_process']
        widgets = {
            'technological_process': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем планы без техкарт и сортируем по сроку выполнения
        self.fields['production_plan'].queryset = ProductionPlan.objects.filter(
            techcard__isnull=True
        ).order_by('deadline')

        # Настраиваем отображение элементов в выпадающем списке
        self.fields['production_plan'].label_from_instance = lambda obj: (
            f"{obj.order_name} | {obj.product} | {obj.customer} | "
            f"Кол-во: {obj.quantity} | Срок: {obj.deadline}"
        )


class TechCardStageForm(forms.ModelForm):
    class Meta:
        model = TechCardStage
        fields = ['name', 'equipment', 'operation_time', 'instructions', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
