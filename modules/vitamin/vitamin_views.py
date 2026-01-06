from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from modules.vitamin.models import Vitamin

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

# ----------------referensi Vitamin--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class VitaminListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Vitamin
    #paginate_by = 5
    permission_required = 'vitamin.view_vitamin'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/referensi/vitamin/vitamin_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/referensi/vitamin/vitamin.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) 
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Vitamin"
        return context
    
    def get_queryset(self):
        qs = self.model.objects.all()
        if self.request.GET.get("q",''):
              qs = self.model.objects.filter(
                 Q(nama__icontains=self.request.GET.get("q",''))
              )
        return qs.order_by('-id')
    
    

class VitaminCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Vitamin
    template_name = 'vitamin/referensi/vitamin/vitamin_form.html'
    form_class = VitaminForm
    success_url = reverse_lazy('vitamin:vitamin-list')
    permission_required = 'vitamin.add_vitamin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Vitamin"
        return context

class VitaminUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Vitamin
    template_name = 'vitamin/referensi/vitamin/vitamin_edit.html'
    form_class = VitaminForm
    success_url = reverse_lazy('vitamin:vitamin-list')
    permission_required = 'vitamin.change_vitamin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Vitamin"
        return context

class VitaminDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Vitamin
    template_name = 'vitamin/referensi/vitamin/vitamin_delete.html'
    success_url = reverse_lazy('vitamin:vitamin-list')
    permission_required = 'vitamin.delete_vitamin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Vitamin"
        return context

class VitaminDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Vitamin
    template_name = 'vitamin/referensi/vitamin/vitamin_detail.html'
    success_url = reverse_lazy('vitamin:vitamin-list')
    permission_required = 'vitamin.view_vitamin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Vitamin"
        print(context)
        return context
    

def download_template(request):
    file_path = os.path.join(settings.BASE_DIR, 'static', 'files', 'template_ref_vitamin.xlsx')
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename='template_ref_vitamin.xlsx')
        return response
    else:
        raise Http404("Template file not found.")
    

def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        # Read Excel file into pandas DataFrame
        try:
            df = pd.read_excel(excel_file, sheet_name='vitamin_obat')

            # Check if 'nama' column exists
            if 'Nama' not in df.columns:
                messages.error(request, "'Nama' column not found in Excel file.")
                return redirect('vitamin:vitamin-list')

            for nama_value in df['Nama'].dropna():  # drop empty rows if any
                Vitamin.objects.create(nama=str(nama_value))

            messages.success(request, "Excel file imported successfully.")
        except Exception as e:
            messages.error(request, f"Error importing file: {e}")

    return redirect('vitamin:vitamin-list')  # Redirect to a success or list page

