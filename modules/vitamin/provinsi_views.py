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
class ProvinsiListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Provinsi
    #paginate_by = 50
    permission_required = 'vitamin.view_provinsi'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/referensi/provinsi/provinsi_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/referensi/provinsi/provinsi.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * 25
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Provinsi"
        return context
    

class ProvinsiCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Provinsi
    template_name = 'vitamin/referensi/provinsi/provinsi_form.html'
    form_class = ProvinsiForm
    success_url = reverse_lazy('vitamin:provinsi-list')
    permission_required = 'vitamin.add_provinsi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Provinsi"
        return context

class ProvinsiUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Provinsi
    template_name = 'vitamin/referensi/provinsi/provinsi_edit.html'
    form_class = ProvinsiForm
    success_url = reverse_lazy('vitamin:provinsi-list')
    permission_required = 'vitamin.change_provinsi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Provinsi"
        return context

class ProvinsiDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Provinsi
    template_name = 'vitamin/referensi/provinsi/provinsi_delete.html'
    success_url = reverse_lazy('vitamin:provinsi-list')
    permission_required = 'vitamin.delete_provinsi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Provinsi"
        return context

class ProvinsiDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Provinsi
    template_name = 'vitamin/referensi/provinsi/provinsi_detail.html'
    success_url = reverse_lazy('vitamin:provinsi-list')
    permission_required = 'vitamin.view_provinsi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Provinsi"
        print(context)
        return context