from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .models import Menu
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator

# ----------------menu--------------------
#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class MenuListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Menu
    permission_required = 'uman.view_menu'
    ordering = ('aplikasi','urutan','name')
    def get_template_names(self):
        if self.request.htmx:
            return ["uman/menu/menu_list.html"] # The response HTML to inject into a list
        else:
            return ["uman/menu/menu.html"] # The actual form

    def get_queryset(self):
        qs = self.model.objects.all().order_by('parent_id','urutan','name')
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Menu"
        return context


class MenuDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Menu
    template_name = 'uman/menu/menu_detail.html'
    success_url = reverse_lazy('uman:menu-list')
    permission_required = 'uman.view_menu'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Detail Menu"
        return context


class MenuCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Menu
    template_name = 'uman/menu/menu_form.html'
    form_class = MenuForm
    success_url = reverse_lazy('uman:menu-list')
    permission_required = 'uman.add_menu'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Menu Baru"
        return context


class MenuDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Menu
    template_name = 'uman/menu/menu_delete.html'
    success_url = reverse_lazy('uman:menu-list')
    permission_required = 'uman.delete_menu'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Menu"
        return context


class MenuUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = Menu
    template_name = 'uman/menu/menu_edit.html'
    form_class = MenuForm
    success_url = reverse_lazy('uman:menu-list')
    permission_required = 'uman.change_menu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Menu"
        return context

