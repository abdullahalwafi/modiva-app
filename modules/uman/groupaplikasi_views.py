from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .models import GroupAplikasi
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin

from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator

# ----------------aplikasi--------------------
#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class GroupAplikasiListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = GroupAplikasi
    permission_required = 'uman.view_groupaplikasi'
    def get_template_names(self):
        if self.request.htmx:
            return ["uman/groupaplikasi/groupaplikasi_list.html"] # The response HTML to inject into a list
        else:
            return ["uman/groupaplikasi/groupaplikasi.html"] # The actual form
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Group Aplikasi"
        return context

class GroupAplikasiCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = GroupAplikasi
    template_name = 'uman/groupaplikasi/groupaplikasi_form.html'
    form_class = GroupAplikasiForm
    success_url = reverse_lazy('uman:groupaplikasi-list')
    permission_required = 'uman.add_groupaplikasi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Group Aplikasi"
        return context

class GroupAplikasiDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = GroupAplikasi
    template_name = 'uman/groupaplikasi/groupaplikasi_delete.html'
    success_url = reverse_lazy('uman:groupaplikasi-list')
    permission_required = 'uman.delete_groupaplikasi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Group Aplikasi"
        return context

class GroupAplikasiUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = GroupAplikasi
    template_name = 'uman/groupaplikasi/groupaplikasi_edit.html'
    form_class = GroupAplikasiForm
    success_url = reverse_lazy('uman:groupaplikasi-list')
    permission_required = 'uman.change_groupaplikasi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Group Aplikasi"
        return context


