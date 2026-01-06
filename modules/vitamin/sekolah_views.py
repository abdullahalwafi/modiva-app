from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from modules.vitamin.models import Sekolah

from modules.core.core_libs import *
from django.contrib.auth.models import Group

from django.contrib.auth.mixins import PermissionRequiredMixin
import logging

logger = logging.getLogger(__name__)
from django.forms import formset_factory
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator
from django.views import View
from datetime import date
from django.core.exceptions import ObjectDoesNotExist

from .forms import *

# ----------------referensi Sekolah--------------------
@method_decorator([group_must_have_permission], name='dispatch')
class SekolahListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Sekolah
    paginate_by = 6
    permission_required = 'vitamin.view_sekolah'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/referensi/sekolah/sekolah_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/referensi/sekolah/sekolah.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) 
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Sekolah"
        kode_sekolah = self.request.user.username
        context["context_list"] = Sekolah.objects.filter(kode=kode_sekolah)
        return context

    def get_queryset(self):
        qs = self.model.objects.all()

        # filter pencarian
        q = self.request.GET.get("q", "")
        if q:
            qs = qs.filter(
                Q(nama__icontains=q) |
                Q(alamat__icontains=q) |
                Q(kelurahan__nama__icontains=q)
            )

        # superuser & admin bisa lihat semua
        if self.request.user.is_superuser or self.request.user.groups.filter(name="administrator").exists():
            return qs.order_by("-id")

        # kalau sekolah → hanya sekolah sesuai kode user
        if self.request.user.groups.filter(name="Sekolah").exists():
            return qs.filter(kode=self.request.user.username).order_by("-id")

        # kalau puskesmas → hanya sekolah mitra
        if self.request.user.groups.filter(name="Puskesmas").exists():
            try:
                puskesmas = Puskesmas.objects.get(kode=self.request.user.username)
                return qs.filter(puskesmas=puskesmas).order_by("-id")
            except Puskesmas.DoesNotExist:
                return qs.none()

        # default: kosong
        return qs.none()
    
@csrf_exempt 
@login_required
def toggle_status_sekolah(request, pk):
    sekolah = get_object_or_404(Sekolah, pk=pk)
    sekolah.status = 0 if sekolah.status == 1 else 1
    sekolah.save()
    return render(request, "vitamin/referensi/sekolah/sekolah_item.html", {"data": sekolah})


class SekolahCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Sekolah
    template_name = 'vitamin/referensi/sekolah/sekolah_form.html'
    form_class = SekolahForm
    success_url = reverse_lazy('vitamin:sekolah-list')
    permission_required = 'vitamin.add_sekolah'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Sekolah"
        return context

class SekolahUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Sekolah
    template_name = 'vitamin/referensi/sekolah/sekolah_edit.html'
    form_class = SekolahForm
    success_url = reverse_lazy('vitamin:sekolah-list')
    permission_required = 'vitamin.change_sekolah'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Sekolah"
        return context

class SekolahDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Sekolah
    template_name = 'vitamin/referensi/sekolah/sekolah_delete.html'
    success_url = reverse_lazy('vitamin:sekolah-list')
    permission_required = 'vitamin.delete_sekolah'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Sekolah"
        return context

class SekolahDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Sekolah
    template_name = 'vitamin/referensi/sekolah/sekolah_detail.html'
    success_url = reverse_lazy('vitamin:sekolah-list')
    permission_required = 'vitamin.view_sekolah'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Sekolah"
        print(context)
        return context