from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_protect
from django.http import request,HttpResponse, HttpResponseRedirect
from django.db.models import Q
from .models import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from datetime import datetime,timedelta
from .forms import KirimForm
from .system_task_service import *
from django.contrib import messages
from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator

# ----------------log menu list--------------------
#@group_must_have_permission <-- kalau funvtion based
@method_decorator([group_must_have_permission], name='dispatch')
class LogMenuListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LogMenu
    permission_required = 'mytask.view_logmenu'

    def get_template_names(self):
        if self.request.htmx:
            return ["mytask/log_menu/log_menu_list.html"] # The response HTML to inject into a list
        else:
            return ["mytask/log_menu/log_menu.html"] # The actual form

    def get_queryset(self):
        tanggal = self.request.GET.get("tanggal",datetime.today().date())
        if self.request.user.is_superuser:
            qs = self.model.objects.filter(created_at__date=tanggal).exclude(menu__url=reverse_lazy('mytask:log-aktifitas')).order_by('-created_at')
        else:
            qs = self.model.objects.filter(created_by=self.request.user.id).filter(created_at__date=tanggal).exclude(menu__url=reverse_lazy('mytask:log-aktifitas')).order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * self.paginate_by
        context["tanggal"] = self.request.GET.get("tanggal",str(datetime.today().date()))
        context["tanggal_terpilih"] = context['tanggal']
        mp_obj = MenuProduk.objects.filter(aktif=True).all()
        menuproduk_list = []
        for mp  in mp_obj:
            for m in mp.menu.all():
                  menuproduk_list.append([m.name,mp.produk.nama]  )
        context["menuproduk_list"] = menuproduk_list 
        context["title"] = "Daftar Log Aktifitas"
        return context

class LogMenuDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = LogMenu
    permission_required = 'mytask.view_logmenu'

    def get_template_names(self):
        if self.request.htmx:
            return ["mytask/log_menu/log_menu_detail.html"] # The response HTML to inject into a list
        else:
            return ["mytask/log_menu/log_menu.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mp_obj = MenuProduk.objects.filter(aktif=True).all()
        for mp  in mp_obj:
            if self.object.menu in mp.menu.all():
                context['produk'] = mp.produk
        context["title"] = "Detail Aktifitas"
        return context

@login_required
@csrf_protect
def DialogKirim(request,pk):
        if request.htmx:
            template_name = "mytask/log_menu/log_menu_kirim_form.html"
        else:
            template_name = "mytask/log_menu/log_menu_kirim.html"
    
        if request.user.is_superuser: 
             lm_obj = LogMenu.objects.filter(pk=pk).first()
        else:
             lm_obj = LogMenu.objects.filter(pk=pk,created_by=request.user.id).first()
        context = dict()
        context['object'] = lm_obj
        mp_obj = MenuProduk.objects.filter(aktif=True).all()
        for mp  in mp_obj:
            if lm_obj.menu in mp.menu.all():
                context['produk'] = mp.produk
        
        
        if request.method == 'POST':
              form = KirimForm(request.POST)
              if form.is_valid():      
                   produk_id = form.cleaned_data["produk_id"]
                   #menu_id = form.cleaned_data["menu_id"]
                   tanggal = form.cleaned_data["tanggal"]
                   waktu_awal = form.cleaned_data["waktu_awal"]
                   waktu_akhir = form.cleaned_data["waktu_akhir"]
                   startTime = f'{tanggal} {waktu_awal}'
                   endTime = f'{tanggal} {waktu_akhir}'
                   date_format = '%Y-%m-%d %H:%M:%S'
                   waktu_selisih = datetime.strptime(endTime, date_format) - datetime.strptime(startTime, date_format)
                   duration = round(waktu_selisih.total_seconds()/60)
                   startTime =  f'{tanggal}T{waktu_awal}Z'
                   endTime = f'{tanggal}T{waktu_akhir}Z'
                   nip = ''
                   try:
                        produk = Produk.objects.get(id=int(produk_id))
                        #nip = request.user.pegawai.nip
                        if request.user.pegawai:
                             nip = request.user.pegawai.nip
                        else:
                             nip = request.user.userdetail.nip
                        if nip == None or nip == '':
                             messages.warning(request,"Pengiriman aktifitas Gagal, pengguna belum ada data NIP nya")
                             return redirect(reverse_lazy('mytask:log-aktifitas'))

                        result = create_mytask(nip, startTime, endTime, duration, produk.produk_id)
                        if result['success']:
                            #messages.info(request,result['data'])
                            messages.info(request,"Pengiriman aktifitas berhasil")
                            HasilKirim(user=request.user,produk=produk,tanggal=tanggal,waktu_awal=waktu_awal,waktu_akhir=waktu_akhir,created_by=request.user.id,updated_by=request.user.id).save()
                        else:
                            messages.error(request,f'Gagal: Pengiriman aktifitas ({produk.nama} untuk user {nip}) tidak berhasil : {result["error"]}')
                        
                   except Exception as e:
                        messages.error(request,'Error: %s'%e)
              else:
                     messages.error(request, form.errors)
              return redirect(reverse_lazy('mytask:log-aktifitas'))

        return render(request,template_name,context)
