from django.views.generic import DetailView
from .models import TechCard


class TechCardDetailView(DetailView):
    model = TechCard
    template_name = 'techcard/detail.html'
    context_object_name = 'techcard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        techcard = self.object

        # Прогресс выполнения
        context['progress_percent'] = round(
            (techcard.total_quantity - techcard.remaining_quantity) / techcard.total_quantity * 100,
            1
        )
        return context
