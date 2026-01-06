from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .models import Jabatan
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator

# ----------------jabatan--------------------
#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class JabatanListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Jabatan
    permission_required = 'uman.view_jabatan'
    ordering = ('nm_jabatan',)
    def get_template_names(self):
        if self.request.htmx:
            return ["uman/jabatan/jabatan_list.html"] # The response HTML to inject into a list
        else:
            return ["uman/jabatan/jabatan.html"] # The actual form
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Jabatan"
        return context

class JabatanDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Jabatan
    template_name = 'uman/jabatan/jabatan_detail.html'
    success_url = reverse_lazy('uman:jabatan-list')
    permission_required = 'uman.view_jabatan'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Datil Jabatan"
        return context

class JabatanCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Jabatan
    template_name = 'uman/jabatan/jabatan_form.html'
    form_class = JabatanForm
    success_url = reverse_lazy('uman:jabatan-list')
    permission_required = 'uman.add_jabatan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Jabatan"
        return context
class JabatanDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Jabatan
    template_name = 'uman/jabatan/jabatan_delete.html'
    success_url = reverse_lazy('uman:jabatan-list')
    permission_required = 'uman.delete_jabatan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Jabatan"
        return context
    #def form_invalid(self, form):
    #    """If the form is invalid, render the invalid form."""
    #    print("ERRROR",form.errors)
    #    return self.render_to_response(self.get_context_data(form=form))

class JabatanUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = Jabatan
    template_name = 'uman/jabatan/jabatan_edit.html'
    form_class = JabatanForm
    success_url = reverse_lazy('uman:jabatan-list')
    permission_required = 'uman.change_jabatan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Jabatan"
        return context
