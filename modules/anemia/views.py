from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from modules.anemia.forms import AnemiaPredictionForm
from modules.anemia.services import AnemiaPredictionError, SELECTED_FEATURES, predict_anemia


class AnemiaAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(name__in=['Administrator', 'Puskesmas']).exists()
        )


class AnemiaInputView(AnemiaAccessMixin, FormView):
    template_name = 'anemia/input.html'
    form_class = AnemiaPredictionForm

    def form_valid(self, form):
        query = '&'.join(
            f'{feature}={form.cleaned_data[feature]}'
            for feature in SELECTED_FEATURES
        )
        return redirect(f'{reverse("anemia:result")}?{query}')


class AnemiaResultView(AnemiaAccessMixin, TemplateView):
    template_name = 'anemia/result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = {feature: self.request.GET.get(feature) for feature in SELECTED_FEATURES}
        form = AnemiaPredictionForm(data=data)
        context['form'] = form
        context['features'] = SELECTED_FEATURES

        if not form.is_valid():
            messages.error(self.request, 'Parameter prediksi tidak lengkap atau tidak valid.')
            context['result_data'] = None
            return context

        try:
            context['result_data'] = predict_anemia(form.as_feature_dict())
        except AnemiaPredictionError as exc:
            messages.error(self.request, str(exc))
            context['result_data'] = None

        return context
