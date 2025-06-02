import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Coalesce
from django.shortcuts import redirect
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView
)
from .forms import ProductionPlanForm
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
import pandas as pd
from .forms import ExcelUploadForm
from django.db.models import Sum, Q, Case, When, FloatField, ExpressionWrapper, F
from .models import ProductionPlan
from django.http import HttpResponse
from io import BytesIO


logger = logging.getLogger(__name__)


class StaffRequiredMixin(LoginRequiredMixin):
    """Проверяет, что пользователь admin/director"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role in ['admin', 'director']:
            return redirect('production_plan:list')
        return super().dispatch(request, *args, **kwargs)


class ProductionPlanListView(LoginRequiredMixin, ListView):
    model = ProductionPlan
    template_name = 'production_plan/list.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            calculated_completed=Coalesce(
                Sum('shift_assignments__actual_quantity',
                    filter=Q(shift_assignments__status='completed')),
                0
            ),
            calculated_progress=ExpressionWrapper(
                F('calculated_completed') * 100.0 / F('quantity'),
                output_field=FloatField()
            )
        ).order_by('-deadline')

        # Добавляем строковое поле с точкой в качестве десятичного разделителя
        for plan in queryset:
            if plan.calculated_progress is not None:
                plan.calculated_progress_str = f"{plan.calculated_progress:.1f}".replace(',', '.')
            else:
                plan.calculated_progress_str = "0"

        return queryset


class ProductionPlanCreateView(StaffRequiredMixin, CreateView):
    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = 'production_plan/create.html'
    success_url = reverse_lazy('production_plan:list')


class ProductionPlanUpdateView(StaffRequiredMixin, UpdateView):
    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = 'production_plan/update.html'
    success_url = reverse_lazy('production_plan:list')


class ProductionPlanDeleteView(StaffRequiredMixin, DeleteView):
    model = ProductionPlan
    template_name = 'production_plan/delete.html'
    success_url = reverse_lazy('production_plan:list')


class ProductionPlanDetailView(LoginRequiredMixin, DetailView):
    model = ProductionPlan
    template_name = 'production_plan/detail.html'


class ProductionPlanUploadView(FormView):
    template_name = 'production_plan/upload.html'
    form_class = ExcelUploadForm
    success_url = reverse_lazy('production_plan:list')

    # Маппинг русских колонок в поля модели
    column_mapping = {
        'Наименование заказа': 'order_name',
        'Заказчик': 'customer',
        'Продукт': 'product',
        'Количество': 'quantity',
        'Номер чертежа': 'drawing_number',
        'Срок': 'deadline',
    }

    required_columns = list(column_mapping.keys())

    def form_valid(self, form):
        excel_file = form.cleaned_data['excel_file']
        try:
            df = pd.read_excel(excel_file)

            # Проверка обязательных колонок
            missing = set(self.required_columns) - set(df.columns)
            if missing:
                messages.error(self.request, f"Отсутствуют обязательные колонки: {', '.join(missing)}")
                return self.form_invalid(form)

            df.rename(columns=self.column_mapping, inplace=True)

            created_count = 0
            error_details = []

            for index, row in df.iterrows():
                try:
                    ProductionPlan.objects.create(
                        order_name=row['order_name'],
                        customer=row['customer'],
                        product=row['product'],
                        quantity=row['quantity'],
                        drawing_number=row['drawing_number'],
                        deadline=row['deadline'],
                    )
                    created_count += 1
                except Exception as e:
                    logger.error(f"Ошибка в строке {index + 2}: {e}")
                    error_details.append(f"Строка {index + 2}: {e}")

            if created_count:
                messages.success(self.request, f"Успешно загружено {created_count} производственных планов.")

            if error_details:
                messages.warning(self.request, f"Не удалось загрузить {len(error_details)} строк:")
                for err in error_details[:3]:
                    messages.error(self.request, err)
                if len(error_details) > 3:
                    messages.info(self.request, f"...и ещё {len(error_details) - 3} ошибок")

        except Exception as e:
            messages.error(self.request, f"Ошибка при обработке файла: {str(e)}")
            logger.error(f"Ошибка загрузки файла: {str(e)}")
            return self.form_invalid(form)

        return super().form_valid(form)


def download_production_plan_template(request):
    # Получаем счётчик из сессии, по умолчанию 0
    count = request.session.get('production_plan_download_count', 0) + 1
    request.session['production_plan_download_count'] = count

    df = pd.DataFrame(columns=[
        'Заказчик',
        'Наименование заказа',
        'Продукт',
        'Количество',
        'Номер чертежа',
        'Срок'
    ])

    df.loc[0] = [
        'ООО "МеталлСтрой"',
        'MS-2023-001',
        'Сталь 20',
        500,
        'Чертёж-123',
        '31.05.2025'
    ]

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Шаблон')
    writer.close()
    output.seek(0)

    filename = f"Образец планов ({count}).xlsx"

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response