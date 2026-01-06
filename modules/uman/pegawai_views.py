from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .models import Pegawai
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from modules.uman.decorators  import group_must_have_permission
from django.contrib import messages
from django.utils.decorators import method_decorator

# ----------------pegawai--------------------
#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class PegawaiListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Pegawai
    permission_required = 'uman.view_pegawai'
    ordering = ('user',)
    def get_template_names(self):
        if self.request.htmx:
            return ["uman/pegawai/pegawai_list.html"] # The response HTML to inject into a list
        else:
            return ["uman/pegawai/pegawai.html"] # The actual form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Pegawai"
        return context

class PegawaiDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Pegawai
    template_name = 'uman/pegawai/pegawai_detail.html'
    success_url = reverse_lazy('uman:pegawai-list')
    permission_required = 'uman.view_pegawai'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Detail Pegawai"
        return context

class PegawaiCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Pegawai
    template_name = 'uman/pegawai/pegawai_form.html'
    form_class = PegawaiForm
    success_url = reverse_lazy('uman:pegawai-list')
    permission_required = 'uman.add_pegawai'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Pegawai"
        return context
    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        self.object.save()
        messages.success(self.request, 'Pegawai was created successfully!')
        return redirect(self.success_url)


class PegawaiDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Pegawai
    template_name = 'uman/pegawai/pegawai_delete.html'
    success_url = reverse_lazy('uman:pegawai-list')
    permission_required = 'uman.delete_pegawai'

    #def form_invalid(self, form):
    #    """If the form is invalid, render the invalid form."""
    #    print("ERRROR",form.errors)
    #    return self.render_to_response(self.get_context_data(form=form))
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Pegawai"
        return context
    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete()
        success_message = "Pegawai was deleted successfully"
        messages.success(self.request,success_message)
        return redirect(success_url)

class PegawaiUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = Pegawai
    template_name = 'uman/pegawai/pegawai_edit.html'
    form_class = PegawaiForm
    success_url = reverse_lazy('uman:pegawai-list')
    permission_required = 'uman.change_pegawai'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Pegawai"
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        self.object.save()
        messages.success(self.request, 'Pegawai was updated successfully!')
        return redirect(self.success_url)

