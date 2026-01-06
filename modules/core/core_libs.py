from modules.uman.models import Menu, UserDetail, Pegawai, Aplikasi
from modules.vitamin.models import Puskesmas, Sekolah
from django.contrib.auth.models import User, Group
import redis
import json
from django.conf import settings
import logging
import re
from datetime import datetime
import json
import requests
from django.db.models import Count
from modules.mytask.models import LogMenu
from datetime import datetime
logger = logging.getLogger(__name__)

def format_rp_currency(amount):
    if amount is None or amount == '' or amount == 0:
        return 0

    thousands_separator = "."
    fractional_separator = ","
    currency = "{:,.2f}".format(float(amount))
    if thousands_separator == ".":
         main_currency, fractional_currency = currency.split(".")[0], currency.split(".")[1]
    new_main_currency = main_currency.replace(",", ".")
    currency = new_main_currency + fractional_separator + fractional_currency
    return currency
def fmt_kode(amount,level=1):
    cuted = amount.split('.')
    if len(cuted) > 1:
        return cuted[level-1]
    else:
        return amount

def UserProfile(request):
    try:
       profil = UserDetail.objects.get(user_id=request.user.id)
       return profil
    except:
       return None

def UserPuskesmas(request):
    try:
       username = User.objects.get(user_id=request.user.id)
       print(f' USER ID : {{user_id}}')
       puskesmas = Puskesmas.objects.get(kode=username)
       return puskesmas
    except:
       return None
    
def UserSekolah(request):
    try:
       username = User.objects.get(user_id=request.user.id)
       sekolah = Sekolah.objects.get(kode=username)
       return sekolah
    except:
       return None

def UserPegawai(request):
    try:
       pegawai = Pegawai.objects.get(user_id=request.user.id)
       return pegawai
    except:
       return None

def root_url():
    return f"/{settings.ROOT_URL}"

def is_url_start_with_http(url):
    try:
        if url.find('http') == 0:
            return True
        else:
            return False
    except:
        return False

def is_absolute_path(path):
    if path.find('http') == 0:
         return True
    re_path = re.search(f"^({root_url()})(.*)",path)
    if re_path:
         return True
    #else:
    #     re_path = re.search(f"^{root_url()}.*/embed\?id=(\d+)$",path)
    #     if re_path:
    #         return True
    else:
         return False

def set_absolute_path(path):
    if path == None or path == '':
          #return root_url()
          return ''
    if not is_absolute_path(path):
         return f"{root_url()}{path}"
    else:
         return path

def id_embed_from_url(path):
    if is_absolute_path(path):
         #re_path = re.search(f"^{root_url()}.*/embed\?id=(\d+)$",path)
         re_path = re.search(f"^{root_url()}.*embed\?id=(\d+)$",path)
    else:
         #re_path = re.search(f"^{root_url()}.*/embed\?id=(\d+)$",root_url()+path)
         re_path = re.search(f"^{root_url()}.*embed\?id=(\d+)$",root_url()+path)
    if re_path:
         try:
            return int(re_path.groups()[0])
         except:
            return None
    else:
         return None


def get_relative_path(path):
    re_path = re.search(f"^({root_url()})(.*)",path)
    if re_path:
        try:
            return re_path.groups()[1].split('?')[0]
        except:
            return None
    return None

def redis_connection():
    redis_client = None
    
    return redis_client

def publish_data_on_redis(redis_client,json_data, channel_name):
    try:
        redis_client.publish(channel_name, json.dumps(json_data))
    except:
        pass

def most_accessed_apps(request,jumlah=5):
    context = []
    if request.user.is_superuser:
        qs = (LogMenu.objects.filter(created_at__year=datetime.today().year).values('menu__aplikasi',).annotate(total=Count('id'),).order_by('-total'))[:jumlah]
    else:
        qs = (LogMenu.objects.filter(created_at__year=datetime.today().year, created_by=request.user.id).values('menu__aplikasi',).annotate(total=Count('id'),).order_by('-total'))[:jumlah]
    if qs:
        for item in qs:
            try:
                 context.append({'aplikasi':Aplikasi.objects.get(id=item['menu__aplikasi']),'total':item['total']})
            except:
                 continue
    return context
