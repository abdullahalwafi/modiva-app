from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from .models import GroupMenu
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator

# ----------------menu--------------------
#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class GroupMenuListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = GroupMenu
    permission_required = 'uman.view_groupmenu'
    def get_template_names(self):
        if self.request.htmx:
            return ["uman/groupmenu/groupmenu_list.html"] # The response HTML to inject into a list
        else:
            return ["uman/groupmenu/groupmenu.html"] # The actual form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar Group Menu"
        return context

class GroupMenuCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = GroupMenu
    template_name = 'uman/groupmenu/groupmenu_form.html'
    form_class = GroupMenuForm
    success_url = reverse_lazy('uman:groupmenu-list')
    permission_required = 'uman.add_groupmenu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Group Menu"
        return context

class GroupMenuDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = GroupMenu
    template_name = 'uman/groupmenu/groupmenu_delete.html'
    success_url = reverse_lazy('uman:groupmenu-list')
    permission_required = 'uman.delete_groupmenu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Group Menu"
        return context

class GroupMenuUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = GroupMenu
    template_name = 'uman/groupmenu/groupmenu_edit.html'
    form_class = GroupMenuForm
    success_url = reverse_lazy('uman:groupmenu-list')
    permission_required = 'uman.change_groupmenu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Group Menu"
        return context
