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

import os
from django.conf import settings
from django.http import FileResponse, Http404
from openpyxl import load_workbook
from io import BytesIO

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
   

from modules.vitamin.models import SiswaHB, Sekolah, Puskesmas
from modules.vitamin.utils.hb_rag_export import export_siswahb_queryset_to_chroma

# ----------------referensi Siswa--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class SiswaHbListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = SiswaHB
    #paginate_by = 10
    permission_required = 'vitamin.view_siswahb'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/sekolah/siswahb/siswahb_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/sekolah/siswahb/siswahb.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) 
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Siswa HB"
        context["is_admin_user"] = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="administrator").exists()
        )
         #-------------awal jika user admin-------------
        app_group = Group.objects.get(name='administrator')

        if not self.request.user.is_superuser and app_group not in self.request.user.groups.all():
            try:
                sekolah_id = Sekolah.objects.get(kode=self.request.user).id
            except Exception as e:
                sekolah_id = 0
            qs = self.model.objects.filter().count()

        else:
            qs = self.model.objects.filter().count() 
        
        context["countsiswahb"] = qs

        return context
    
    def get_queryset(self):
        qs = self.model.objects.select_related("siswa__sekolah").order_by('-tahun')

        if self.request.user.is_superuser or self.request.user.groups.filter(name="administrator").exists():
            return qs

        if self.request.user.groups.filter(name="Sekolah").exists():
            try:
                sekolah = Sekolah.objects.get(kode=self.request.user.username)
                return qs.filter(siswa__sekolah=sekolah).order_by('-tahun')
            except Sekolah.DoesNotExist:
                return qs.none()

        if self.request.user.groups.filter(name="Puskesmas").exists():
            try:
                puskesmas = Puskesmas.objects.get(kode=self.request.user.username)
                return qs.filter(siswa__sekolah__puskesmas=puskesmas).order_by('-tahun')
            except Puskesmas.DoesNotExist:
                return qs.none()

        return qs.none()



class SiswaHbCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = SiswaHB
    template_name = 'vitamin/sekolah/siswahb/siswahb_form.html'
    form_class = SiswaHbForm
    success_url = reverse_lazy('vitamin:siswahb-list')
    permission_required = 'vitamin.add_siswahb'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Siswa HB"
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # ✅ Pass the logged-in user to the form
        return kwargs

class SiswaHbUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = SiswaHB
    template_name = 'vitamin/sekolah/siswahb/siswahb_edit.html'
    form_class = SiswaHbForm
    success_url = reverse_lazy('vitamin:siswahb-list')
    permission_required = 'vitamin.change_siswahb'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Siswa HB"
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # ✅ Pass the logged-in user to the form
        return kwargs

class SiswaHbDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = SiswaHB
    template_name = 'vitamin/sekolah/siswahb/siswahb_delete.html'
    success_url = reverse_lazy('vitamin:siswahb-list')
    permission_required = 'vitamin.delete_siswahb'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Siswa HB"
        return context

class SiswaHbDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = SiswaHB
    template_name = 'vitamin/sekolah/siswahb/siswahb_detail.html'
    success_url = reverse_lazy('vitamin:siswahb-list')
    permission_required = 'vitamin.view_siswahb'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Siswa HB"
        print(context)
        return context
    

def download_template(request):
    template_path = os.path.join(settings.BASE_DIR, 'static', 'files', 'template_siswa_hb.xlsx')
    
    if not os.path.exists(template_path):
        raise Http404("Template file not found.")

    # Load the workbook
    wb = load_workbook(template_path)
    
    ### === Sheet: siswa === ###
    siswa_sheet = 'siswa'
    if siswa_sheet not in wb.sheetnames:
        raise Http404(f"Sheet '{siswa_sheet}' not found in template.")
    ws_siswa = wb[siswa_sheet]

    # Clear existing vitamin sheet data (rows after header)
    for row in ws_siswa.iter_rows(min_row=2, max_row=ws_siswa.max_row):
        for cell in row:
            cell.value = None

        # Get user's associated puskesmas_id
    try:
        # Assume the username corresponds to Puskesmas.kode
        kode = request.user.username
        sekolah = Sekolah.objects.get(kode=kode)
        sekolah_id = sekolah.id
    except Sekolah.DoesNotExist:
        messages.error(request, "Sekolah not found for the current user.")
        return redirect('vitamin:siswahb-list')

    # Write Vitamin data
    siswa_data = Siswa.objects.filter(
        sekolah_id=sekolah_id).select_related('siswa', 'sekolah').values_list(
    'id', 'nis', 'nama', 'sekolah__nama')

    for idx, (id, nis, nama, sekolah_nama) in enumerate(siswa_data, start=2):
        ws_siswa.cell(row=idx, column=1).value = id
        ws_siswa.cell(row=idx, column=2).value = nis
        ws_siswa.cell(row=idx, column=3).value = nama
        ws_siswa.cell(row=idx, column=4).value = sekolah_nama

    # Save workbook to memory stream
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # Return as downloadable file
    response = FileResponse(output, as_attachment=True, filename='template_siswa_hb.xlsx')
    return response

def to_hb(val, default=None):
    if pd.isna(val) or val == '':
        return default
    try:
        d = Decimal(str(val).replace(',', '.')).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        return d
    except (InvalidOperation, ValueError):
        return default

def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        try:
            df = pd.read_excel(excel_file, sheet_name='siswa_hb')

            required_columns = {
                'Id Siswa','Tahun','Hb','Keterangan'

            }

            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                messages.error(request, f"Missing columns in Excel file: {', '.join(missing)}")
                return redirect('vitamin:siswahb-list')

            for _, row in df.iterrows():
                try:

                    if pd.isna(row['Id Siswa']) or pd.isna(row['Id Siswa']):
                        continue

                    siswa= Siswa.objects.get(pk=int(row['Id Siswa']))

                    SiswaHB.objects.create(
                    tahun = int(row['Tahun']) if not pd.isna(row['Tahun']) else 2000,
                    hb = to_hb(row['Hb']),  # Decimal(4,1)
                    keterangan = str(row['Keterangan']).strip() if not pd.isna(row['Keterangan']) else '',
                    # pilih salah satu dari dua baris di bawah ini:
                    siswa_id = int(row['Id Siswa'])  # jika CSV punya kolom siswa_id
                    # siswa = siswa_objek                # jika kamu sudah pegang instance Siswa
                        )
                except Exception as e:
                    print(f"❌ Error creating distribusi entry: {e}")

            messages.success(request, "Excel file imported successfully.")

        except Exception as e:
            messages.error(request, f"Error importing file: {e}")

    return redirect('vitamin:siswahb-list')
 
@login_required
def export_hb_to_rag(request):
    # hanya admin atau superuser
    if not (request.user.is_superuser or request.user.groups.filter(name="administrator").exists()):
        messages.error(request, "Kamu tidak memiliki izin untuk export ke RAG.")
        return redirect("vitamin:siswahb-list")

    # pakai scope yang sama seperti ListView supaya konsisten
    qs = SiswaHB.objects.select_related("siswa__sekolah").order_by("-tahun")

    # kalau mau: admin export semuanya, superadmin juga semuanya
    # kalau suatu saat mau admin export per wilayah, tinggal filter di sini.

    try:
        total = export_siswahb_queryset_to_chroma(qs)
        messages.success(request, f"Export ke RAG berhasil. Total data HB diekspor: {total}")
    except Exception as e:
        messages.error(request, f"Gagal export ke RAG: {e}")

    return redirect("vitamin:siswahb-list")
