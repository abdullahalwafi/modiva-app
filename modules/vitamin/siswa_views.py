from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from modules.vitamin.models import Siswa

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

import pandas as pd
from django.http import HttpResponse
import os
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib import messages

from django.utils import timezone

import os
from django.conf import settings
from django.http import FileResponse, Http404
from openpyxl import load_workbook
from io import BytesIO

# ----------------referensi Siswa--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class SiswaListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Siswa
    #paginate_by = 10
    permission_required = 'vitamin.view_siswa'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/sekolah/siswa/siswa_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/sekolah/siswa/siswa.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) 
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Siswa"
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
        
        context["countsiswa"] = qs

        return context
    
    def get_queryset(self):
        app_group = Group.objects.get(name='administrator')

        # kalau admin atau superuser → semua siswa
        if self.request.user.is_superuser or app_group in self.request.user.groups.all():
            return self.model.objects.all().order_by('-id')

        # kalau user dari Sekolah → hanya siswa di sekolah itu
        if self.request.user.groups.filter(name="Sekolah").exists():
            try:
                sekolah_id = Sekolah.objects.get(kode=self.request.user.username).id
                return self.model.objects.filter(sekolah_id=sekolah_id).order_by('-id')
            except Sekolah.DoesNotExist:
                return self.model.objects.none()

        # kalau user dari Puskesmas → tampilkan semua siswa dari sekolah-sekolah mitra puskesmas tersebut
        if self.request.user.groups.filter(name="Puskesmas").exists():
            try:
                puskesmas = Puskesmas.objects.get(kode=self.request.user.username)
                sekolah_ids = Sekolah.objects.filter(puskesmas=puskesmas).values_list('id', flat=True)
                return self.model.objects.filter(sekolah_id__in=sekolah_ids).order_by('-id')
            except Puskesmas.DoesNotExist:
                return self.model.objects.none()

        # default: kosong
        return self.model.objects.none()
    
    

class SiswaCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Siswa
    template_name = 'vitamin/sekolah/siswa/siswa_form.html'
    form_class = SiswaForm
    success_url = reverse_lazy('vitamin:siswa-list')
    permission_required = 'vitamin.add_siswa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Siswa"
        return context
    
    def form_valid(self, form):
        obj = form.save(commit=False)
        #puskesmas_id = UserPuskesmas(self.request)
        #print(f' PUSKESMAS KODE {self.request.user}')
        user = self.request.user

        # These should ideally be based on request data
        obj.sekolah= Sekolah.objects.get(kode=user)

        obj.created_by = self.request.user.id  # Make sure you have a FK to User
        obj.created_at = timezone.now()

        obj.save()
        return super().form_valid(form)

class SiswaUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Siswa
    template_name = 'vitamin/sekolah/siswa/siswa_edit.html'
    form_class = SiswaForm
    success_url = reverse_lazy('vitamin:siswa-list')
    permission_required = 'vitamin.change_siswa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Siswa"
        return context
    
    def form_valid(self, form):
        obj = form.save(commit=False)
        #puskesmas_id = UserPuskesmas(self.request)
        #print(f' PUSKESMAS KODE {self.request.user}')
        user = self.request.user

        # These should ideally be based on request data
        obj.sekolah= Sekolah.objects.get(kode=user)

        obj.created_by = self.request.user.id  # Make sure you have a FK to User
        obj.created_at = timezone.now()

        obj.save()
        return super().form_valid(form)

class SiswaDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Siswa
    template_name = 'vitamin/sekolah/siswa/siswa_delete.html'
    success_url = reverse_lazy('vitamin:siswa-list')
    permission_required = 'vitamin.delete_siswa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Siswa"
        return context

class SiswaDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Siswa
    template_name = 'vitamin/sekolah/siswa/siswa_detail.html'
    success_url = reverse_lazy('vitamin:siswa-list')
    permission_required = 'vitamin.view_siswa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Siswa"
        print(context)
        return context
    
def download_template(request):
    template_path = os.path.join(settings.BASE_DIR, 'static', 'files', 'template_siswa.xlsx')
    
    if not os.path.exists(template_path):
        raise Http404("Template file not found.")

    # Load the workbook
    wb = load_workbook(template_path)
    
    # Save workbook to memory stream
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # Return as downloadable file
    response = FileResponse(output, as_attachment=True, filename='template_siswa.xlsx')
    return response


def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        try:
            df = pd.read_excel(excel_file, sheet_name='siswa')

            required_columns = {
                'NIS', 'Nama', 'Tempat Lahir', 'Tanggal Lahir', 'Email', 'Jenis Kelamin (Isi L atau P)' 
            }

            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                messages.error(request, f"Missing columns in Excel file: {', '.join(missing)}")
                return redirect('vitamin:siswa-list')

            # Get sekolah by user.username     
            try:
                sekolah = Sekolah.objects.get(kode=request.user.username)
            except Sekolah.DoesNotExist:
                messages.error(request, "Sekolah not found for the current user.")
                return redirect('vitamin:siswa-list')
            
            for _, row in df.iterrows():
                try:

                    Siswa.objects.create(
                        nis=str(row['NIS']),
                        nama=str(row['Nama']),
                        tmp_lahir=str(row['Tempat Lahir']),
                        tgl_lahir=pd.to_datetime(row['Tanggal Lahir']) if not pd.isna(row['Tanggal Lahir']) else None,
                        email=str(row['Email']),
                        gender=str(row['Jenis Kelamin (Isi L atau P)']),
                        sekolah=sekolah
                    )
                except Exception as e:
                    print(f"❌ Error creating distribusi entry: {e}")

            messages.success(request, "Excel file imported successfully.")

        except Exception as e:
            messages.error(request, f"Error importing file: {e}")

    return redirect('vitamin:siswa-list')