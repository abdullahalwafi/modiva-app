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

import pandas as pd
from django.http import HttpResponse
import os
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib import messages

# ----------------referensi Satuan--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class SatuanListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Satuan
    #paginate_by = 5
    permission_required = 'vitamin.view_satuan'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/referensi/satuan/satuan_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/referensi/satuan/satuan.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * self.paginate_by
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) 
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Satuan"
        return context
    
    def get_queryset(self):
        qs = self.model.objects.all()
        if self.request.GET.get("q",''):
              qs = self.model.objects.filter(
                 Q(nama__icontains=self.request.GET.get("q",'')) |
                 Q(keterangan__icontains=self.request.GET.get("q",''))
              )
        return qs.order_by('-id')
    

class SatuanCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Satuan
    template_name = 'vitamin/referensi/satuan/satuan_form.html'
    form_class = SatuanForm
    success_url = reverse_lazy('vitamin:satuan-list')
    permission_required = 'vitamin.add_satuan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Satuan"
        return context

class SatuanUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Satuan
    template_name = 'vitamin/referensi/Satuan/Satuan_edit.html'
    form_class = SatuanForm
    success_url = reverse_lazy('vitamin:satuan-list')
    permission_required = 'vitamin.change_Satuan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Satuan"
        return context

class SatuanDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Satuan
    template_name = 'vitamin/referensi/satuan/satuan_delete.html'
    success_url = reverse_lazy('vitamin:satuan-list')
    permission_required = 'vitamin.delete_satuan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Satuan"
        return context

class SatuanDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Satuan
    template_name = 'vitamin/referensi/satuan/satuan_detail.html'
    success_url = reverse_lazy('vitamin:satuan-list')
    permission_required = 'vitamin.view_satuan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Satuan"
        print(context)
        return context
    
def download_template(request):
    file_path = os.path.join(settings.BASE_DIR, 'static', 'files', 'template_ref_satuan.xlsx')
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename='template_ref_satuan.xlsx')
        return response
    else:
        raise Http404("Template file not found.")
    

def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        # Read Excel file into pandas DataFrame
        try:
            df = pd.read_excel(excel_file, sheet_name='satuan')

            required_columns = {'Nama', 'Keterangan'}

            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                messages.error(request, f"Missing columns in Excel file: {', '.join(missing)}")
                return redirect('vitamin:satuan-list')

                # Loop through rows and create objects
            for _, row in df.iterrows():
                nama_val = row['Nama']
                ket_val = row['Keterangan']

                # Skip rows where nama is empty/null
                if pd.isna(nama_val):
                    continue

                Satuan.objects.create(
                    nama=str(nama_val),
                    keterangan=str(ket_val) if not pd.isna(ket_val) else ''
                )

            messages.success(request, "Excel file imported successfully.")
        except Exception as e:
            messages.error(request, f"Error importing file: {e}")

    return redirect('vitamin:satuan-list')  # Redirect to a success or list page