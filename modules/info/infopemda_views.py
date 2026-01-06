from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Q

from .models import InfoPemda
from modules.core.core_libs import *
from modules.uman.decorators  import group_must_have_permission
from .forms import *

# Create your views here.
@method_decorator([group_must_have_permission], name='dispatch')
class InfoPemdaView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = InfoPemda
    permission_required = 'info.view_infopemda'
    ordering = ('created_at','updated_at','keterangan')
    def get_template_names(self):
        if self.request.htmx:
            return ["info/infopemda/infopemda_list.html"] # The response HTML to inject into a list
        else:
            return ["info/infopemda/infopemda.html"] # The actual form
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Daftar Informasi'
        return context

    def get_queryset(self):
        user_pemda = UserPemda(self.request)
        user_groups = self.request.user.groups.all()
        if self.request.user.is_superuser:
             qs = self.model.objects.all().order_by('-created_at','keterangan','file_pdf')
        elif user_pemda:
             qs = self.model.objects.filter(Q(penerima__isnull=True)|Q(penerima__exact=None) | (Q(groupmenu__group__in=user_groups)&Q(penerima__exact=user_pemda))).distinct().order_by('-created_at','keterangan','file_pdf')
        else:
             qs = self.model.objects.none()
        return qs

class InfoPemdaCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = InfoPemda
    template_name = 'info/infopemda/infopemda_form.html'
    form_class = InfoPemdaForm
    success_url = reverse_lazy('info:infopemda-list')
    permission_required = 'info.add_infopemda'
    def get_template_names(self):
        if self.request.htmx:
            return ["info/infopemda/infopemda_form_partial.html"] # The response HTML to inject into a list
        else:
            return ["info/infopemda/infopemda_form.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Tambah Informasi'
        return context
class InfoPemdaDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = InfoPemda
    template_name = 'info/infopemda/infopemda_delete.html'
    success_url = reverse_lazy('info:infopemda-list')
    permission_required = 'info.delete_infopemda'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Hapus Informasi'
        return context


class InfoPemdaUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = InfoPemda
    template_name = 'info/infopemda/infopemda_edit.html'
    success_url = reverse_lazy('info:infopemda-list')
    permission_required = 'info.change_infopemda'
    form_class = InfoPemdaForm
    def get_template_names(self):
        if self.request.htmx:
            return ["info/infopemda/infopemda_edit_partial.html"] # The response HTML to inject into a list
        else:
            return ["info/infopemda/infopemda_edit.html"] # The actual form
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ubah Informasi'
        return context
