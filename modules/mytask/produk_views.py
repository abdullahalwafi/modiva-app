from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q
from .models import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from datetime import datetime
from .forms import *
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator


# ----------------log menu list--------------------

#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class ProdukListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Produk
    permission_required = 'mytask.view_produk'

    def get_template_names(self):
        if self.request.htmx:
            return ["mytask/produk/produk_list.html"] # The response HTML to inject into a list
        else:
            return ["mytask/produk/produk.html"] # The actual form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Produk"
        return context

class ProdukCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Produk
    template_name = 'mytask/produk/produk_form.html'
    form_class = ProdukForm
    success_url = reverse_lazy('mytask:produk-list')
    permission_required = 'mytask.add_produk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Produk"
        return context

class ProdukUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Produk
    template_name = 'mytask/produk/produk_edit.html'
    form_class = ProdukForm
    success_url = reverse_lazy('mytask:produk-list')
    permission_required = 'mytask.change_produk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Produk"
        return context

class ProdukDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Produk
    template_name = 'mytask/produk/produk_delete.html'
    success_url = reverse_lazy('mytask:produk-list')
    permission_required = 'mytask.delete_produk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Produk"
        return context

class ProdukDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Produk
    template_name = 'mytask/produk/produk_detail.html'
    success_url = reverse_lazy('mytask:produk-list')
    permission_required = 'mytask.view_produk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Produk"
        print(context)
        return context


