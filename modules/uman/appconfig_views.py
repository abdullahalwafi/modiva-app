from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request, HttpResponseRedirect
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from modules.uman.decorators import group_must_have_permission
from django.utils.decorators import method_decorator

from .models import AppConfig

# ----------------appconfig--------------------
@method_decorator([group_must_have_permission], name='dispatch')
class AppConfigListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AppConfig
    permission_required = 'uman.view_appconfig'

    def get_template_names(self):
        if self.request.htmx:
            # The response HTML to inject into a list
            return ["uman/appconfig/appconfig_list.html"]
        else:
            return ["uman/appconfig/appconfig.html"]  # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Parameter Konfigurasi"
        return context


class AppConfigCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = AppConfig
    template_name = 'uman/appconfig/appconfig_form.html'
    success_url = reverse_lazy('uman:appconfig-list')
    permission_required = 'uman.add_appconfig'
    fields = ['namespace', 'key', 'value', 'description']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Buat Parameter Konfigurasi baru"
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save(commit=False)
        self.object.save()
        messages.success(self.request, 'AppConfig was created successfully!')
        return redirect(self.success_url)


class AppConfigUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = AppConfig
    template_name = 'uman/appconfig/appconfig_edit.html'
    success_url = reverse_lazy('uman:appconfig-list')
    permission_required = 'uman.change_appconfig'
    fields = ['namespace', 'key', 'value', 'description']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Paramater Konfigurasi"
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save(commit=False)
        self.object.save()
        messages.success(self.request, 'AppConfig was updated successfully!')
        return redirect(self.success_url)


class AppConfigDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = AppConfig
    template_name = 'uman/appconfig/appconfig_delete.html'
    success_url = reverse_lazy('uman:appconfig-list')
    permission_required = 'uman.delete_appconfig'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Parameter Konfigurasi"
        return context

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(self.request, 'AppConfig was deleted successfully!')

        return HttpResponseRedirect(success_url)
