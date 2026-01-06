from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .models import EmbedMenu
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin
import logging

logger = logging.getLogger(__name__)

from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator

# ----------------menu--------------------
#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class EmbedMenuListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = EmbedMenu
    permission_required = 'uman.view_embedmenu'
    def get_template_names(self):
        if self.request.htmx:
            return ["uman/embedmenu/embedmenu_list.html"] # The response HTML to inject into a list
        else:
            return ["uman/embedmenu/embedmenu.html"] # The actual form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Embed Menu"
        return context

class EmbedMenuDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = EmbedMenu
    template_name = 'uman/embedmenu/embedmenu_detail.html'
    success_url = reverse_lazy('uman:embedmenu-list')
    permission_required = 'uman.view_embedmenu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Detail Embed Menu"
        return context

class EmbedMenuCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = EmbedMenu
    template_name = 'uman/embedmenu/embedmenu_form.html'
    form_class = EmbedMenuForm
    success_url = reverse_lazy('uman:embedmenu-list')
    permission_required = 'uman.add_embedmenu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Embed Menu"
        return context

class EmbedMenuDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = EmbedMenu
    template_name = 'uman/embedmenu/embedmenu_delete.html'
    success_url = reverse_lazy('uman:embedmenu-list')
    permission_required = 'uman.delete_embedmenu'

    def form_valid(self,form):
        logger.info('#### Gagal delete Embed menu')
        return super(EmbedMenuDeleteView, self).form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Embed Menu"
        return context


class EmbedMenuUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = EmbedMenu
    template_name = 'uman/embedmenu/embedmenu_edit.html'
    form_class = EmbedMenuForm
    success_url = reverse_lazy('uman:embedmenu-list')
    permission_required = 'uman.change_embedmenu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Embed Menu"
        return context


