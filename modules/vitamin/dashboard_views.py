from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from modules.vitamin.models import Satuan

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
from django.db.models import Sum

# ----------------referensi Satuan--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class DisObatListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Distribusiobat
    paginate_by = 50
    permission_required = 'vitamin.view_distribusiobat'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/dashboard_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/dashboard.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * self.paginate_by
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Distribusi Obat"
        
        puskesmas_id = self.request.GET.get('id', '0')

        sekolah_id = self.request.GET.get('id', '0')

        #-------------awal jika user admin-------------
        app_group = Group.objects.get(name='Administrator')

        app_group2 = Group.objects.get(name='Puskesmas')

        app_group3 = Group.objects.get(name='Sekolah')

        if not self.request.user.is_superuser and app_group not in self.request.user.groups.all():
            if app_group2 in self.request.user.groups.all():
                try:
                    puskesmas_id = Puskesmas.objects.get(kode=self.request.user).id
                except Exception as e:
                    puskesmas_id = 0
                qs = self.model.objects.filter(puskesmas_id=puskesmas_id).count()
                
                total_distribusi = Distribusiobat.objects.filter(puskesmas_id=puskesmas_id).aggregate(total=Sum('jumlah_terima'))['total'] or 0
                total_stok = Stokobat.objects.filter(puskesmas_id=puskesmas_id).aggregate(total=Sum('stok'))['total'] or 0
                total_distsiswa = 0
                total_sekolah = Distribusiobat.objects.filter(puskesmas_id=puskesmas_id).values('sekolah_id').distinct().count()
            elif app_group3 in self.request.user.groups.all():
                try:
                    sekolah_id = Sekolah.objects.get(kode=self.request.user).id
                except Exception as e:
                    sekolah_id = 0
                qs = self.model.objects.filter(sekolah_id=sekolah_id).count()
                total_distribusi = Distribusisiswa.objects.filter(sekolah_id=sekolah_id).count() or 0
                total_stok = Distribusiobat.objects.filter(sekolah_id=sekolah_id).aggregate(total=Sum('stok'))['total'] or 0
                total_distsiswa = Distribusisiswa.objects.filter(sekolah_id=sekolah_id).count() or 0
                total_sekolah = Distribusiobat.objects.filter(sekolah_id=sekolah_id).aggregate(total=Sum('jumlah_terima'))['total'] or 0
            else:
                print(f' TIDAK ADA')

        else:
            qs = self.model.objects.filter().count() 
            total_distribusi = Distribusiobat.objects.aggregate(total=Sum('jumlah_terima'))['total'] or 0
            total_stok = Stokobat.objects.aggregate(total=Sum('stok'))['total'] or 0
            total_distsiswa = Distribusisiswa.objects.count()
            total_sekolah = Distribusiobat.objects.values('sekolah_id').distinct().count()

            print(f' JUMLAH : {qs}')
        
        context["count2"] = qs
        context["total_distribusi"] = total_distribusi
        context["total_stok"] = total_stok
        context["total_distsiswa"] = total_distsiswa
        context["total_sekolah"] = total_sekolah


        return context
    
    
    def get_queryset(self):

        #-------------awal jika user admin-------------
        app_group = Group.objects.get(name='administrator')


        if not self.request.user.is_superuser and app_group not in self.request.user.groups.all():
            try:
                puskesmas_id = Puskesmas.objects.get(kode=self.request.user).id
            except Exception as e:
                puskesmas_id = 0
            qs = self.model.objects.filter(puskesmas_id=puskesmas_id).order_by('-tgl_terima','-id')
            return qs

        else:
            qs = self.model.objects.filter().order_by('-tgl_terima','-id')

            return qs
        # -------------akhir jika user admin------
    
@method_decorator([group_must_have_permission], name='dispatch')
class StokObatListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Stokobat
    paginate_by = 50
    permission_required = 'vitamin.view_stokobat'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/puskesmas/stokobat/stokobat_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/puskesmas/stokobat/stokobat.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * self.paginate_by
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Stok Obat"
        
        puskesmas_id = self.request.GET.get('id', '0')

        #-------------awal jika user admin-------------
        app_group = Group.objects.get(name='administrator')

        if not self.request.user.is_superuser and app_group not in self.request.user.groups.all():
            try:
                puskesmas_id = Puskesmas.objects.get(kode=self.request.user).id
            except Exception as e:
                puskesmas_id = 0
            qs = self.model.objects.filter(puskesmas_id=puskesmas_id).count()

        else:
            qs = self.model.objects.filter().count() 
        
        context["count"] = qs

        return context
    
    
    def get_queryset(self):
        
        user_id = self.request.user.id

        #-------------awal jika user admin-------------
        app_group = Group.objects.get(name='administrator')

        print(self.request.user.is_superuser)
        print(self.request.user.groups.all())

        if not self.request.user.is_superuser and app_group not in self.request.user.groups.all():
            try:
                print(user_id)
                print(self.request.user)
                puskesmas_id = Puskesmas.objects.get(kode=self.request.user).id
                print(puskesmas_id)
                print('AAAAAAAAAAA')
            except Exception as e:
                puskesmas_id = 0
                print('BBBBBBBBBB')
            qs = self.model.objects.filter(puskesmas_id=puskesmas_id).order_by('-tgl_terima','-id')
            return qs

        else:
            qs = self.model.objects.filter().order_by('-tgl_terima','-id')
            print('AAAAAAAAAAA2222222222')

            return qs
        # -------------akhir jika user admin------

@method_decorator([group_must_have_permission], name='dispatch')
class DistSiswaListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Distribusisiswa
    paginate_by = 50
    permission_required = 'vitamin.view_distribusisiswa'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/sekolah/distsiswa/distsiswa_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/sekolah/distsiswa/distsiswa.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * self.paginate_by
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Distribusi Siswa"
        sekolah_id = self.request.GET.get('id', '0')

        #-------------awal jika user admin-------------
        app_group = Group.objects.get(name='administrator')

        if not self.request.user.is_superuser and app_group not in self.request.user.groups.all():
            try:
                sekolah_id = Sekolah.objects.get(kode=self.request.user).id
            except Exception as e:
                sekolah_id = 0
            qs = self.model.objects.filter(sekolah_id=sekolah_id).count()

        else:
            qs = self.model.objects.filter().count() 
        
        context["countdistsiswa"] = qs

        return context
    
    def get_queryset(self):

        #-------------awal jika user admin-------------
        app_group = Group.objects.get(name='administrator')


        if not self.request.user.is_superuser and app_group not in self.request.user.groups.all():
            try:
                sekolah_id = Sekolah.objects.get(kode=self.request.user).id
            except Exception as e:
                sekolah_id = 0
            qs = self.model.objects.filter(sekolah_id=sekolah_id).order_by('-tgl_terima','-id')
            return qs

        else:
            qs = self.model.objects.filter().order_by('-tgl_terima','-id')

            return qs
        # -------------akhir jika user admin------

def dashboard_superadmin_form(request):
    return render(request, 'vitamin/dashboard_superadmin_form.html')
