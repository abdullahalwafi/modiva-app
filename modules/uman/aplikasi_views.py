from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .models import Aplikasi
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin

# ----------------aplikasi--------------------
class AplikasiListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Aplikasi
    permission_required = 'uman.view_aplikasi'
    def get_template_names(self):
        if self.request.htmx:
            return ["uman/aplikasi/aplikasi_list.html"] # The response HTML to inject into a list
        else:
            return ["uman/aplikasi/aplikasi.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Aplikasi"
        return context

class AplikasiDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Aplikasi
    template_name = 'uman/aplikasi/aplikasi_detail.html'
    success_url = reverse_lazy('uman:aplikasi-list')
    permission_required = 'uman.view_aplikasi'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Detail Aplikasi"
        return context


class AplikasiCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Aplikasi
    template_name = 'uman/aplikasi/aplikasi_form.html'
    form_class = AplikasiForm
    success_url = reverse_lazy('uman:aplikasi-list')
    permission_required = 'uman.add_aplikasi'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Aplikasi"
        return context


class AplikasiDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Aplikasi
    template_name = 'uman/aplikasi/aplikasi_delete.html'
    success_url = reverse_lazy('uman:aplikasi-list')
    permission_required = 'uman.delete_aplikasi'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Aplikasi"
        return context


class AplikasiUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = Aplikasi
    template_name = 'uman/aplikasi/aplikasi_edit.html'
    form_class = AplikasiForm
    success_url = reverse_lazy('uman:aplikasi-list')
    permission_required = 'uman.change_aplikasi'
    """
    def form_invalid(self, form):
        print("ERRROR",form.errors)
        return self.render_to_response(self.get_context_data(form=form))

    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Aplikasi"
        return context

