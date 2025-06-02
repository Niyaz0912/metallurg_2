from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import TechCard, TechCardStage
from .forms import TechCardForm, TechCardStageForm
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin


# Миксин для ограничения доступа директору
class DirectorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_director  # замените на вашу логику


class TechCardListView(DirectorRequiredMixin, ListView):
    model = TechCard
    template_name = 'techcard/list.html'
    context_object_name = 'techcards'


class TechCardCreateView(DirectorRequiredMixin, CreateView):
    model = TechCard
    form_class = TechCardForm
    template_name = 'techcard/create.html'
    success_url = reverse_lazy('techcard:list')


class TechCardUpdateView(DirectorRequiredMixin, UpdateView):
    model = TechCard
    form_class = TechCardForm
    template_name = 'techcard/update.html'
    success_url = reverse_lazy('techcard:list')


class TechCardDeleteView(DirectorRequiredMixin, DeleteView):
    model = TechCard
    template_name = 'techcard/delete.html'
    success_url = reverse_lazy('techcard:list')


class TechCardDetailView(LoginRequiredMixin, DetailView):
    model = TechCard
    template_name = 'techcard/detail.html'
    context_object_name = 'techcard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        techcard = self.object

        completed = techcard.production_plan.completed_quantity
        total = techcard.total_quantity

        progress = (completed / total) * 100 if total > 0 else 0

        # Преобразуем progress в строку с точкой как десятичным разделителем
        progress_str = f"{progress:.1f}".replace(',', '.')

        context['progress_percent'] = progress
        context['progress_percent_str'] = progress_str

        return context


# CRUD для этапов (пример для создания)
class TechCardStageCreateView(DirectorRequiredMixin, CreateView):
    model = TechCardStage
    form_class = TechCardStageForm
    template_name = 'techcard/stage_form.html'

    def form_valid(self, form):
        techcard = TechCard.objects.get(pk=self.kwargs['techcard_pk'])
        form.instance.techcard = techcard
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('techcard:detail', kwargs={'pk': self.kwargs['techcard_pk']})

