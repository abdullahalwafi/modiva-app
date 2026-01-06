from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from modules.vitamin.models import Puskesmas

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
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

from .forms import *

# ----------------referensi Puskesmas--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class PuskesmasListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = Puskesmas
    paginate_by = 6
    permission_required = 'vitamin.view_puskesmas'

    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/referensi/puskesmas/puskesmas_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/referensi/puskesmas/puskesmas.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) 
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Puskesmas"
        kode_puskesmas = self.request.user.username
        context["context_list"] = Puskesmas.objects.filter(kode=kode_puskesmas)
        return context
    
    def get_queryset(self):
        qs = self.model.objects.all()
        if self.request.GET.get("q",''):
              qs = self.model.objects.filter(
                 Q(nama__icontains=self.request.GET.get("q",'')) |
                 Q(alamat__icontains=self.request.GET.get("q",'')) |
                 Q(kelurahan__nama__icontains=self.request.GET.get("q",'')) 
              )
        return qs.order_by('-is_terdaftar')
    
@csrf_exempt 
@login_required
def toggle_status_puskesmas(request, pk):
    puskesmas = get_object_or_404(Puskesmas, pk=pk)
    puskesmas.is_terdaftar = 0 if puskesmas.is_terdaftar == 1 else 1
    puskesmas.save()
    return render(request, "vitamin/referensi/puskesmas/puskesmas_item.html", {"data": puskesmas})


class PuskesmasCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Puskesmas
    template_name = 'vitamin/referensi/puskesmas/puskesmas_form.html'
    form_class = PuskesmasForm
    success_url = reverse_lazy('vitamin:puskesmas-list')
    permission_required = 'vitamin.add_puskesmas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tambah Puskesmas"
        return context

class PuskesmasUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Puskesmas
    template_name = 'vitamin/referensi/puskesmas/puskesmas_edit.html'
    form_class = PuskesmasForm
    success_url = reverse_lazy('vitamin:puskesmas-list')
    permission_required = 'vitamin.change_puskesmas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Puskesmas"
        return context
    
class PuskesmasUpdateView2(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Puskesmas
    template_name = 'vitamin/referensi/puskesmas/puskesmas_edit_status.html'
    form_class = PuskesmasForm2
    success_url = reverse_lazy('vitamin:puskesmas-list')
    permission_required = 'vitamin.change_puskesmas'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_terdaftar = 0  # Set is_terdaftar ke 0
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Nonaktifkan Puskesmas"
        return context

class PuskesmasDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = Puskesmas
    template_name = 'vitamin/referensi/puskesmas/puskesmas_delete.html'
    success_url = reverse_lazy('vitamin:puskesmas-list')
    permission_required = 'vitamin.delete_puskesmas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Puskesmas"
        return context

class PuskesmasDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Puskesmas
    template_name = 'vitamin/referensi/puskesmas/puskesmas_detail.html'
    success_url = reverse_lazy('vitamin:puskesmas-list')
    permission_required = 'vitamin.view_puskesmas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail Puskesmas"
        context["sekolah"] = self.model.objects.get(id=self.kwargs.get('pk')).sekolah_set.all()
        print(context)
        return context


def ListPuskesmasByKode(request,pk):
    username = request.user.username  # Get the current logged-in user's username
    print(f'Logged-in user: {username}')

    # Find the Puskesmas where the kode matches the username
    puskesmas = get_object_or_404(Puskesmas, kode=username)
    print(f'Found Puskesmas ID: {puskesmas.id}')

    return render(request, 'includes/modiva_sidebar3.html', {
        'puskesmas_id': puskesmas.id
    })


def profilpuskesmas(request,pk):
    # Assuming user has a field called `kode_puskesmas`
    kode_puskesmas = request.user.username
    Listpuskesmasbylogin = Puskesmas.objects.filter(kode=kode_puskesmas).all

    print(f' AA { Listpuskesmasbylogin }')


    return render(request, 'includes/modiva_sidebar3.html', {
        'puskesmas_id': Listpuskesmasbylogin
    })


    