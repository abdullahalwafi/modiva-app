from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_protect
from django.http import request,HttpResponse, HttpResponseRedirect
from django.db.models import Q
from .models import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from datetime import datetime,timedelta
from django.contrib import messages
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator

# ----------------List hasil kirim aktifitas--------------------
#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class HasilKirimListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = HasilKirim
    permission_required = 'mytask.view_hasilkirim'

    def get_template_names(self):
        if self.request.htmx:
            return ["mytask/hasil_kirim/hasil_kirim_list.html"] # The response HTML to inject into a list
        else:
            return ["mytask/hasil_kirim/hasil_kirim.html"] # The actual form

    def get_queryset(self):
        tanggal = self.request.GET.get("tanggal",datetime.today().date())
        if self.request.user.is_superuser:
            qs = self.model.objects.filter(created_at__date=tanggal).order_by('-created_at')
        else:
            qs = self.model.objects.filter(created_by=self.request.user.id).filter(created_at__date=tanggal).order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * self.paginate_by
        context["tanggal"] = self.request.GET.get("tanggal",str(datetime.today().date()))
        context["tanggal_terpilih"] = context['tanggal']
        context["title"]="Daftar History Hasil Kirim Aktifitas"
        return context
