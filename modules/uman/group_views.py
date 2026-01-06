from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages


@method_decorator([group_must_have_permission], name='dispatch')
class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    permission_required = 'auth.view_group'
    ordering = ('name')
    def get_template_names(self):
        if self.request.htmx:
            return ['uman/group/group_list.html'] # The response HTML to inject into a list
        else:
            return ['uman/group/group.html'] # The actual form
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Group"
        return context


class GroupCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Group
    template_name = 'uman/group/group_form.html'
    form_class = GroupCreateForm
    success_url = reverse_lazy('uman:group-list')
    permission_required = 'auth.add_group'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Group"
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save(commit=False)
        permissions = [ int(perm) for perm in self.request.POST.getlist('permission') ]
        self.object.save()
        self.object.permissions.set(permissions)
        self.object.save()
       
        messages.success(self.request, 'Group was created successfully!')
        return redirect(self.success_url)

class GroupDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Group
    template_name = 'uman/group/group_delete.html'
    success_url = reverse_lazy('uman:group-list')
    permission_required = 'auth.add_group'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Group"
        return context
    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete()
        success_message = "Group was deleted successfully"
        messages.success(self.request,success_message)
        return HttpResponseRedirect(success_url)


class GroupUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Group
    template_name = 'uman/group/group_edit.html'
    form_class = GroupUpdateForm
    success_url = reverse_lazy('uman:group-list')
    permission_required = 'auth.change_group'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Group"
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save(commit=False)
        permissions = [ int(perm) for perm in self.request.POST.getlist('permission') ]
        self.object.save()
        self.object.permissions.set(permissions)
        self.object.save()

        messages.success(self.request, 'Group was updated successfully!')
        return redirect(self.success_url)

class GroupDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Group
    template_name = 'uman/group/group_detail.html'
    success_url = reverse_lazy('uman:group-list')
    permission_required = 'auth.view_group'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Detail Group"
        return context
