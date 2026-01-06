from modules.uman.models import Menu, UserDetail, Aplikasi, GroupAplikasi, Pegawai

from django.conf import settings
from django.db.models import Q
import re
from modules.core.core_libs import root_url, is_absolute_path, set_absolute_path, id_embed_from_url, get_relative_path

def menu_renderer(request):
    return {
       'all_menu': Menu.objects.all().order_by('urutan','parent_id'),
    }


def Applications(request):
    context = {'aplikasi':None,'grupapp':None}
    aplikasi = Aplikasi.objects.filter(aktif=True).order_by('group_id','-urutan')
    grupapp = GroupAplikasi.objects.filter(aktif=True).order_by('-urutan')
    if aplikasi:
        context["aplikasi"] = aplikasi
    if grupapp:
        context["grupapp"] = grupapp
    return context

def BreadDict(request):
    fullpath = request.get_full_path()
    path = request.path
    menu = None
    breadcrumb = []
    if path != '':
        #re_path = re.search(f"^/{settings.ROOT_URL}.*/embed\?id=(\d+)$",path)
        id_embed = id_embed_from_url(fullpath)
        if id_embed:
              try:
                  menu = Menu.objects.filter(id=id_embed,aktif=True).first()
              except:
                  menu = None
        else:
              try:
                  menu = Menu.objects.filter(Q(url__exact=path)|Q(url__exact=get_relative_path(path))).first() 
              except:
                  raise
                  menu = None
    if menu:
            breadcrumb = [menu]
            m = menu
            for i in range(6):
               try:
                   breadcrumb.insert(0,m.parent)
                   m = m.parent
               except:
                   breadcrumb.insert(0,menu)
                   break
    return {'bread':breadcrumb}

