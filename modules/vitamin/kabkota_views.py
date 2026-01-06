from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from modules.vitamin.models import Provinsi

from modules.core.core_libs import *
from django.contrib.auth.models import Group

from django.contrib.auth.mixins import PermissionRequiredMixin
import logging

logger = logging.getLogger(__name__)
from django.forms import formset_factory
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator
from django.views import View
from datetime import date
from django.core.exceptions import ObjectDoesNotExist

from .forms import *

# ----------------referensi provinsi--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class KabKotaListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = KabKota
    #paginate_by = 50
    permission_required = 'vitamin.view_kabkota'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/referensi/kabkota/kabkota_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/referensi/kabkota/kabkota.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * 25
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar KabKota"
        return context
    

class KabKotaCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = KabKota
    template_name = 'vitamin/referensi/kabkota/kabkota_form.html'
    form_class = KabKotaForm
    success_url = reverse_lazy('vitamin:kabkota-list')
    permission_required = 'vitamin.add_kabkota'

    def form_valid(self, form):
        obj = form.save(commit=False)
        #obj_prov = Provinsi.objects.get(kd_prov=obj.provinsi_id)
     
        #obj.province_id = obj_prov.kd_prov
        obj.id = obj.provinsi_id+""+obj.id
        obj.save()
        return super(KabKotaCreateView, self).form_valid(form)

    def form_invalid(self, form):
        return super(KabKotaCreateView, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah KabKota"
        return context

class KabKotaUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = KabKota
    template_name = 'vitamin/referensi/kabkota/kabkota_edit.html'
    form_class = KabKotaForm
    success_url = reverse_lazy('vitamin:kabkota-list')
    permission_required = 'vitamin.change_kabkota'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah KabKota"
        return context

class KabKotaDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = KabKota
    template_name = 'vitamin/referensi/kabkota/kabkota_delete.html'
    success_url = reverse_lazy('vitamin:kabkota-list')
    permission_required = 'vitamin.delete_kabkota'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus KabKota"
        return context

class KabKotaDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = KabKota
    template_name = 'vitamin/referensi/kabkota/kabkota_detail.html'
    success_url = reverse_lazy('vitamin:kabkota-list')
    permission_required = 'vitamin.view_kabkota'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail KabKota"
        print(context)
        return context