from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from modules.vitamin.models import Kelurahan

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

# ----------------referensi Kelurahan--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class KelurahanListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Kelurahan
    paginate_by = 50
    permission_required = 'vitamin.view_kelurahan'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/referensi/kelurahan/kelurahan_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/referensi/kelurahan/kelurahan.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) 
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Kelurahan"
        return context
    

class KelurahanCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Kelurahan
    template_name = 'vitamin/referensi/kelurahan/kelurahan_form.html'
    form_class = KelurahanForm
    success_url = reverse_lazy('vitamin:kelurahan-list')
    permission_required = 'vitamin.add_kelurahan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Kelurahan"
        return context

class KelurahanUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Kelurahan
    template_name = 'vitamin/referensi/kelurahan/kelurahan_edit.html'
    form_class = KelurahanForm
    success_url = reverse_lazy('vitamin:kelurahan-list')
    permission_required = 'vitamin.change_kelurahan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Kelurahan"
        return context

class KelurahanDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Kelurahan
    template_name = 'vitamin/referensi/kelurahan/kelurahan_delete.html'
    success_url = reverse_lazy('vitamin:kelurahan-list')
    permission_required = 'vitamin.delete_kelurahan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Kelurahan"
        return context

class KelurahanDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Kelurahan
    template_name = 'vitamin/referensi/kelurahan/kelurahan_detail.html'
    success_url = reverse_lazy('vitamin:kelurahan-list')
    permission_required = 'vitamin.view_kelurahan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Kelurahan"
        print(context)
        return context