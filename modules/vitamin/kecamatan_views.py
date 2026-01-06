from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from modules.vitamin.models import Kecamatan

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

# ----------------referensi kecamatan--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class KecamatanListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Kecamatan
    #paginate_by = 50
    permission_required = 'vitamin.view_kecamatan'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/referensi/kecamatan/kecamatan_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/referensi/kecamatan/kecamatan.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * 25
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Kecamatan"
        return context
    
    def get_queryset(self):
        qs = self.model.objects.all()
        if self.request.GET.get("q",''):
              qs = self.model.objects.filter(
                 Q(nama__icontains=self.request.GET.get("q",''))
              )
        return qs.order_by('-id')
    

class KecamatanCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Kecamatan
    template_name = 'vitamin/referensi/kecamatan/kecamatan_form.html'
    form_class = KecamatanForm
    success_url = reverse_lazy('vitamin:kecamatan-list')
    permission_required = 'vitamin.add_kecamatan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Kecamatan"
        return context

class KecamatanUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Kecamatan
    template_name = 'vitamin/referensi/kecamatan/kecamatan_edit.html'
    form_class = KecamatanForm
    success_url = reverse_lazy('vitamin:kecamatan-list')
    permission_required = 'vitamin.change_Kecamatan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Kecamatan"
        return context

class KecamatanDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Kecamatan
    template_name = 'vitamin/referensi/kecamatan/kecamatan_delete.html'
    success_url = reverse_lazy('vitamin:kecamatan-list')
    permission_required = 'vitamin.delete_kecamatan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Kecamatan"
        return context

class KecamatanDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Kecamatan
    template_name = 'vitamin/referensi/kecamatan/kecamatan_detail.html'
    success_url = reverse_lazy('vitamin:kecamatan-list')
    permission_required = 'vitamin.view_kecamatan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Kecamatan"
        print(context)
        return context