from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from .models import ProductionPlan
from django.core.exceptions import ValidationError
from django.utils import timezone


class ProductionPlanForm(forms.ModelForm):
    class Meta:
        model = ProductionPlan
        fields = [
            'customer',
            'order_name',
            'product',
            'quantity',
            'drawing_number',
            'deadline'
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'customer': _('Заказчик'),
            'order_name': _('Номер заказа'),
            'product': _('Изделие'),
            'quantity': _('Количество'),
            'drawing_number': _('Чертеж/Модель'),
            'deadline': _('Срок выполнения'),
        }
        help_texts = {
            'order_name': _('Введите номер или название заказа'),
            'drawing_number': _('Номер чертежа или 3D-модели'),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now().date():
            raise ValidationError(_("Срок выполнения не может быть в прошлом"))
        return deadline

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise ValidationError(_("Количество должно быть положительным числом"))
        return quantity


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label=_('Файл Excel'),
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        help_text=_("Поддерживаются только файлы .xlsx или .xls"),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError(_("Файл слишком большой (максимум 5 МБ)"))
        return file


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Выберите Excel файл')
