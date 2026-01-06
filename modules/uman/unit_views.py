from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .models import Unit
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator

# ----------------unit--------------------
#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class UnitListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Unit
    permission_required = 'uman.view_unit'
    ordering = ('nm_unit',)
    def get_template_names(self):
        if self.request.htmx:
            return ["uman/unit/unit_list.html"] # The response HTML to inject into a list
        else:
            return ["uman/unit/unit.html"] # The actual form
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Unit"
        return context



class UnitDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Unit
    template_name = 'uman/unit/unit_detail.html'
    success_url = reverse_lazy('uman:unit-list')
    permission_required = 'uman.view_unit'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Detil Unit"
        return context

class UnitCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Unit
    template_name = 'uman/unit/unit_form.html'
    form_class = UnitForm
    success_url = reverse_lazy('uman:unit-list')
    permission_required = 'uman.add_unit'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Unit"
        return context


class UnitDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Unit
    template_name = 'uman/unit/unit_delete.html'
    success_url = reverse_lazy('uman:unit-list')
    permission_required = 'uman.delete_unit'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Unit"
        return context

    #def form_invalid(self, form):
    #    """If the form is invalid, render the invalid form."""
    #    print("ERRROR",form.errors)
    #    return self.render_to_response(self.get_context_data(form=form))

class UnitUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = Unit
    template_name = 'uman/unit/unit_edit.html'
    form_class = UnitForm
    success_url = reverse_lazy('uman:unit-list')
    permission_required = 'uman.change_unit'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Unit"
        return context
