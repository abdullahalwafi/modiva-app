from django.shortcuts import render, redirect, reverse
# Create your views here.
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request, HttpResponseRedirect
from django.db.models import Q
from django.conf import settings
import requests
from requests.auth import HTTPBasicAuth
from django.contrib import messages
from modules.uman.models import Menu, Aplikasi
import pandas
from datetime import datetime
from modules.uman.decorators import *
from modules.mytask.models import *
from modules.info.models import *
from django.utils.decorators import method_decorator
#from .core_libs import UserPemda, get_summary_tkdd, get_summary_apbd, most_accessed_apps, get_table_tkdd, get_table_apbd
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import cache_control
import jwt
import time
#from modules.core.core_context_processor import UserDetails
import logging

logger = logging.getLogger(__name__)


def metabaseIframeUrl(m, request):
    # METABASE_SITE_URL = "http://localhost:3000"
    # METABASE_SECRET_KEY = "964fac8cd8efae15b751bcf9c7d544ac736de5a4686724e918748eff007f60d5"
    METABASE_SITE_URL = m.url_metabase
    METABASE_SECRET_KEY = m.secretkey
    params = {}
    #if m.param_kementerian:
    #    params['kementerian'] = ''
    #    kementerian = Kementerian.objects.filter(
    #        aktif=True, kode=request.user.userdetail.kd_kementerian).first()
    #    if kementerian:
    #        params['kementerian'] = kementerian.nama

   

    if METABASE_SECRET_KEY and METABASE_SITE_URL and m.metabase_id:
        payload = {
            "resource": {"dashboard": m.metabase_id},
            "params": params,
            "exp": round(time.time()) + (60 * 10)  # 10 minute expiration
        }
        token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")
        iframeUrl = METABASE_SITE_URL + "/embed/dashboard/" + \
            token + "#bordered=true&titled=true"
    else:
        iframeUrl = None
    return iframeUrl


def index(request):
    template_name = 'core/index.html'
    title = 'Index page'
    data = {'page_title': title, 'message': 'Hello Dunia'}

    return render(request, template_name, context=data)


@method_decorator([group_must_have_permission], name='dispatch')
class EmbedView(LoginRequiredMixin, ListView):
    context = {}
    model = Menu
    template_name = 'core/embed/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = ''
        try:
            context['menu'] = Menu.objects.get(
                id=int(self.request.GET['id']), aktif=True)
            em = context['menu'].embedmenu_set.all()
            if em:
                context['mbiframe_url'] = metabaseIframeUrl(
                    em[0], self.request)
        except:
            # raise
            context['menu'] = None
            messages.warning(self.request, 'Halaman tidak ditemukan')
        return context


@login_required
@group_must_have_permission
def apbd_from_api(request):
    template_name = 'core/apbd_api/apbd_api.html'
    context = {}
    tahun = int(datetime.today().year)-1

    if request.method == 'POST':
        tahun = request.POST.get('tahun')
    # logic akses web api di mesin/komputer lain
    tahun_terpilih = int(tahun)

    url_endpoint = f'{settings.API_BASE_URLS["APBD"]}/ra?tahun={tahun}'
    try:
        page = requests.get(url_endpoint)

        # context['object_list'] = page.json()['results']
        context['object_list'] = page.json()
        # ---- end here -----
        df = pandas.json_normalize(page.json())

        dt = df.groupby(['namapropinsi']).sum('anggaran')
        dx = dt.sort_values(by='anggaran', ascending=False).head(10)
        data_total_a = dx.loc[:, ['anggaran', 'realisasi']].sum().to_dict()
        data = dx.loc[:, ['anggaran', 'realisasi']].to_dict()

        data2 = df.filter(items=['anggaran', 'realisasi']).sum().to_dict()

        context['anggaran'] = data['anggaran']
        context['realisasi'] = data['realisasi']
        context['tahun_terpilih'] = tahun_terpilih
        context['list_tahun'] = range(
            int(datetime.today().year)-5, int(datetime.today().year)+5)

        total_a = data2['anggaran']
        data_a = data['anggaran']
        data_a_persen = {}
        for k in data_a:
            data_a_persen[k] = '%.2f' % ((data_a[k]/total_a)*100)

        total_r = data2['realisasi']
        data_r = data['realisasi']
        data_r_persen = {}
        for k in data_r:
            data_r_persen[k] = '%.2f' % ((data_r[k]/total_a)*100)

        total = data2['anggaran']+data2['realisasi']

        context['data_ra'] = data_a_persen
        context['data_rr'] = data_r_persen

        # print(data_r_persen)
        # print(total_a)
    except:
        context['tahun_terpilih'] = tahun_terpilih
        context['list_tahun'] = range(
            int(datetime.today().year) - 5, int(datetime.today().year)+5)
        logger.critical(
            f'Gagal Koneksi ke endpoint APBD API {settings.API_BASE_URLS["APBD"]}/ra?tahun={tahun}')
        messages.error(
            request, 'Koneksi ke endpoint APBD API sepertinya tidak dapat tersambung!')
        return render(request, template_name, context=context)
    # context['object_list'] = page.json()['results']
    context['object_list'] = page.json()
    context['tahun_terpilih'] = tahun_terpilih
    context['list_tahun'] = range(
        int(datetime.today().year)-5, int(datetime.today().year)+5)
    # ---- end here -----
    df = pandas.json_normalize(page.json())
    try:
        dt = df.groupby(['namapropinsi']).sum('anggaran')
        dx = dt.sort_values(by='anggaran', ascending=False).head(10)
        data_total_a = dx.loc[:, ['anggaran', 'realisasi']].sum().to_dict()
        data = dx.loc[:, ['anggaran', 'realisasi']].to_dict()

        data2 = df.filter(items=['anggaran', 'realisasi']).sum().to_dict()

        context['anggaran'] = data['anggaran']
        context['realisasi'] = data['realisasi']

        total_a = data2['anggaran']
        data_a = data['anggaran']
        data_a_persen = {}
        for k in data_a:
            data_a_persen[k] = '%.2f' % ((data_a[k]/total_a)*100)

        total_r = data2['realisasi']
        data_r = data['realisasi']
        data_r_persen = {}
        for k in data_r:
            data_r_persen[k] = '%.2f' % ((data_r[k]/total_a)*100)

        total = data2['anggaran']+data2['realisasi']

        context['data_ra'] = data_a_persen
        context['data_rr'] = data_r_persen
    except:
        logger.critical(
            f'Tidak ada data pada APBD API dengan kueri {settings.API_BASE_URLS["APBD"]}/ra?tahun={tahun}')
        messages.error(
            request, 'Tidak ada data pada APBD API dengan kueri yang dimaksud')

    return render(request, template_name, context=context)


@login_required
@group_must_have_permission
def tkd_from_api(request):
    template_name = 'core/tkd_api/tkd_api.html'
    context = {}
    tahun = int(datetime.today().year)-1

    if request.method == 'POST':
        tahun = request.POST.get('tahun')
    tahun_terpilih = int(tahun)

    # logic akses web api di mesin/komputer lain
    url_endpoint = f'{settings.API_BASE_URLS["TKD"]}/pagu?tahun={tahun}'
    try:
        page = requests.get(url_endpoint)

        # context['object_list'] = page.json()['results']

        # ---- end here -----

        df = pandas.json_normalize(page.json())
        dt = df.groupby(['namapemda']).sum('penyaluran')
        dx = dt.sort_values(by='penyaluran', ascending=False).head(10)
        data = dx.loc[:, ['penyaluran', 'pagu']].to_dict()
        context['pagu'] = data['pagu']
        context['penyaluran'] = data['penyaluran']
        context['tahun_terpilih'] = tahun_terpilih
        context['list_tahun'] = range(
            int(datetime.today().year)-5, int(datetime.today().year)+5)

        context['object_list'] = {}
        for k in data['pagu']:
            context['object_list'][k] = [
                data['pagu'][k], data['penyaluran'][k]]

    except:
        context['tahun_terpilih'] = tahun_terpilih
        context['list_tahun'] = range(
            int(datetime.today().year) - 5, int(datetime.today().year)+5)
        logger.critical(
            f'Gagal Koneksi ke endpoint TKD API {settings.API_BASE_URLS["TKD"]}/pagu?tahun={tahun}')
        messages.error(
            request, 'Koneksi ke endpoint TKD API sepertinya tidak dapat tersambung!')
        return render(request, template_name, context=context)
    # context['object_list'] = page.json()['results']
    context['tahun_terpilih'] = tahun_terpilih
    context['list_tahun'] = range(
        int(datetime.today().year)-5, int(datetime.today().year)+5)
    # ---- end here -----

    df = pandas.json_normalize(page.json())
    try:
        dt = df.groupby(['namapemda']).sum('penyaluran')
        dx = dt.sort_values(by='penyaluran', ascending=False).head(10)
        data = dx.loc[:, ['penyaluran', 'pagu']].to_dict()
        context['pagu'] = data['pagu']
        context['penyaluran'] = data['penyaluran']

        context['object_list'] = {}
        for k in data['pagu']:
            context['object_list'][k] = [
                data['pagu'][k], data['penyaluran'][k]]
    except:
        logger.critical(
            f'Tidak ada data pada TKD API dengan kueri {settings.API_BASE_URLS["TKD"]}/pagu?tahun={tahun}')
        messages.error(
            request, 'Tidak ada data pada TKD API dengan kueri dimaksud!')
    return render(request, template_name, context=context)


def custom_permission_denied_view(request, exception=None):
    messages.error(request, 'Permission Denied !!!')
    return render(request, "errors/403.html", {})


@group_must_have_permission
@login_required
def layanan(request):
    context = {}
    context['aplikasis'] = Aplikasi.objects.filter(
        aktif=True).order_by('urutan', 'name')
    template_name = 'core/layanan.html'
    if request.htmx:
        template_name = 'core/layanan_partial.html'
    return render(request, template_name, context)


@group_must_have_permission
@login_required
@cache_control(private=True, max_age=300)
def landing_page(request):
    context = {}
    context['title'] = ' '
    context['tahun_list'] = range(1990, datetime.today().year+1)
    context['tahun_terpilih'] = datetime.today().year
    tahun = request.GET.get('tahun')
    if tahun and len(tahun) > 0:
        tahun = int(tahun)
    else:
        tahun = int(context['tahun_terpilih'])
    # context['aplikasis'] = Aplikasi.objects.filter(aktif=True).order_by('urutan','name')
    context['aplikasis'] = most_accessed_apps(request, 5)
    log = LogMenu.objects.filter(created_at__date=datetime.today(
    ), created_by=request.user.id).prefetch_related().order_by('created_at', 'menu')
    logmenu = None
    lm_list = []
    for lm in log:
        if lm.menu != logmenu:
            try:
                prod = MenuProduk.objects.get(menu=lm.menu)
            except:
                prod = None
            if prod:
                jam = lm.created_at.hour
                if jam <= 9:
                    style = 'success'
                elif jam > 9 and jam <= 12:
                    style = 'primary'
                elif jam > 12 and jam < 15:
                    style = 'warning'
                else:
                    style = 'danger'

                lm_list.append(
                    {'logmenu': lm, 'menuproduk': prod, 'style': style})
                logmenu = lm.menu
        else:
            continue
    context['mytasks'] = lm_list[:10]
    user_pemda = UserPemda(request)
    user_groups = request.user.groups.all()
    if request.user.is_superuser:
        infopemda = InfoPemda.objects.all().order_by(
            '-created_at', 'keterangan', 'file_pdf')[:10]
    elif user_pemda:
        infopemda = InfoPemda.objects.filter(Q(penerima__isnull=True) | Q(penerima__exact=None) | (Q(groupmenu__group__in=user_groups) & Q(
            penerima__exact=user_pemda))).distinct().order_by('-created_at', 'keterangan', 'file_pdf')[:10]
    else:
        infopemda = InfoPemda.objects.none()
    context['infopemda'] = infopemda
    try:
        context['tkdd'] = get_summary_tkdd(request, tahun)
    except Exception as e:
        messages.error(request, 'Gagal membaca Postur TKDD')
        context['tkdd'] = None
    try:
        context['apbd'] = get_summary_apbd(request, tahun)
    except Exception as e:
        messages.error(request, 'Gagal membaca Postur APBD')
        context['apbd'] = None
    try:
        context['tkdd_table'] = get_table_tkdd(request, tahun)
    except Exception as e:
        messages.error(request, f'Gagal membaca Tabel TKDD: {e}')
        context['tkdd_table'] = None
    try:
        context['apbd_table'] = get_table_apbd(request, tahun)
    except Exception as e:
        messages.error(request, f'Gagal membaca Tabel APBD: {e}')
        context['apbd_table'] = None

    template_name = 'core/landing_page.html'
    context['tahun'] = tahun
    context['tahun_sebelumnya'] = int(tahun) - 1
    if request.htmx:
        template_name = 'core/landing_page_partial.html'
    return render(request, template_name, context)
