from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .models import MenuProduk
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin


class MenuProdukCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = MenuProduk
    template_name = 'mytask/menuproduk/menuproduk_form.html'
    form_class = MenuProdukForm
    success_url = reverse_lazy('mytask:produk-list')
    permission_required = 'mytask.add_menuproduk'

    def get(self, request, *args, **kwargs):
         if self.request.GET.get('produk',None):
              mp =  MenuProduk.objects.filter(produk_id=int(self.request.GET.get('produk'))).first()
              if mp:
                   return redirect(reverse_lazy('mytask:menuproduk-edit',kwargs={'pk':mp.id} ))
         self.object = None
         return super().get(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["produk"] = Produk.objects.filter(id=self.request.GET.get("produk")).first()
        context["title"] = "Tambah produk"
        return context

    

class MenuProdukUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = MenuProduk
    template_name = 'mytask/menuproduk/menuproduk_edit.html'
    form_class = MenuProdukForm
    success_url = reverse_lazy('mytask:produk-list')
    permission_required = 'mytask.change_menuproduk'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["produk"] = Produk.objects.filter(id=self.request.GET.get("produk")).first()
        context["title"] = "Update menu produk"
        return context


"""
class MenuProdukListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = MenuProduk
    permission_required = 'mytask.view_menuproduk'
    def get_template_names(self):
        if self.request.htmx:
            return ["mytask/menuproduk/menuproduk_list.html"] # The response HTML to inject into a list
        else:
            return ["mytask/menuproduk/menuproduk.html"] # The actual form

class MenuProdukDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = MenuProduk
    template_name = 'mytask/menuproduk/menuproduk_delete.html'
    form_class = MenuProdukForm
    success_url = reverse_lazy('mytask:menuproduk-list')
    permission_required = 'mytask.delete_menuproduk'

"""
