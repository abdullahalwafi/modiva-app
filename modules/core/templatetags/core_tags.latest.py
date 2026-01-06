from django import template
from django.template.loader import get_template
from modules.uman.models import Menu, EmbedMenu, GroupMenu, UserDetail, Aplikasi
from modules.core.models import LogDokUpload, Pemda
from django.conf import settings
from django.shortcuts import reverse
from django.db.models import Q
from modules.core.core_libs import root_url, is_url_start_with_http, is_absolute_path, set_absolute_path, id_embed_from_url, get_relative_path
import re
register = template.Library()

@register.simple_tag
def get_root_url():
    return settings.ROOT_URL

@register.simple_tag
def make_absolute_path(url):
    return set_absolute_path(url)

@register.simple_tag
def url_start_with_http(url):
    return is_url_start_with_http(url)

@register.simple_tag
def show_group(user):
    grp = None
    try:
       #grp =  user.groups.all()[0].name
       grps =  [ g.name for g in user.groups.all() ]
       grp = ",".join(grps)
       
    except:
        grp = 'no group'
    return  grp


@register.simple_tag
def namaPemda(request):
    
    try:
        profil = UserDetail.objects.get(user_id=request.user.id)
        pemda = Pemda.objects.get(kd_satker=profil.kode_satker)
        return pemda.nm_pemda
    except:
        return request.user.username

@register.filter
def cekHistoryExist(data):
    
    try:
        obj =  LogDokUpload.objects.filter(dokumen_pemda_id=data.id)
        if obj:
            return 'Exist'
        else:
           
            return None
        
    except:
        return None

def menu_have_childs(menu):
    childs = Menu.objects.filter(parent=menu,aktif=True)
    if childs:
        return True
    else:
        return False

def show_ng_menu(path='',user=None):
    gmenu = []
    top_menu = []
    if user.is_superuser:
        top_menu = Menu.objects.filter(aktif=True,aplikasi__aktif=True,parent=None).order_by('urutan','name').prefetch_related()
        gmenu = Menu.objects.filter(aktif=True,aplikasi__aktif=True).exclude(parent=None).order_by('urutan','name').prefetch_related()
    else:
        group_menu = GroupMenu.objects.filter(group__in=user.groups.all()).prefetch_related()
        for gm in group_menu:
            for m_ in gm.menu.all().exclude(Q(aplikasi__aktif=False)|Q(aktif=False)).order_by('urutan','name').prefetch_related():
                 if m_.parent == None:
                       if m_ in top_menu:
                          continue
                       else:
                          top_menu.append(m_)
                 else:
                       if m_ in gmenu:
                          continue
                       else:
                          gmenu.append(m_)
    context = {}
    html = ''
    menu_active = None
    uri = []
    id_embed = None
    if path != '':
        id_embed = id_embed_from_url(path)
        if id_embed:
                  menu_active = Menu.objects.filter(id=id_embed,aktif=True,aplikasi__aktif=True).first()
        else:
             menu_active = Menu.objects.filter(aktif=True,aplikasi__aktif=True).filter(Q(url__exact=path)|Q(url__exact=get_relative_path(path))).first()

    for tm in top_menu:
        active = ''
        try:
            if tm == menu_active or tm == menu_active.parent or tm == menu_active.parent.parent or tm == menu_active.parent.parent.parent :
                active = 'active'
        except:
              active = ''
        html = html + """<div class="tab-pane fade %s show" id="kt_header_navs_tab_%s">
                         <!--begin::Menu wrapper-->
				<div class="header-menu flex-column align-items-stretch flex-lg-row">
				 <!--begin::Menu-->
                                   <div class="menu menu-rounded menu-column menu-lg-row menu-root-here-bg-desktop menu-active-bg menu-title-gray-700 menu-state-primary menu-arrow-gray-400 fw-semibold align-items-stretch flex-grow-1 px-2 px-lg-0" id="#kt_header_menu" data-kt-menu="true">\n"""%(active,tm.id)

        for m in Menu.objects.filter(parent=tm,id__in=[mn.id for mn in gmenu]).order_by('urutan','name'):
            
            #print('##### Menu active:%s ,Aplikasi active: %s, #### menu:%s , #### aplikais:%s'%(menu_active,menu_active,m,app.name))
            if m == menu_active:
                 text_primary=" text-primary"
            else:
                 try:
                      if m == menu_active.parent:
                              text_primary=" text-primary"
                      else:
                              text_primary=""
                 except:
                       text_primary=""

            if not menu_have_childs(m):
                   target = ''
                   url = set_absolute_path(m.url)
                   try:
                       if m.isembed:
                           url = f"{url}?id={m.id}"
                   except:
                       pass
                   if is_url_start_with_http(url):
                         target = " target='_blank' "

                   html = html + """<div data-kt-menu-placement="bottom-start" class="menu-item me-0 me-lg-2">
                   <!--begin:Menu link-->
                   <span class="menu-link py-3">
                   <span class="menu-title"><A href="%s" %s class="menu-link%s">%s</A></span>
                   <span class="menu-arrow d-lg-none"></span>
                   </span></div>\n"""%(url,target,text_primary,m.name)
                   continue 
            else:
                   if Menu.objects.filter(parent=m,id__in=[ m_.id for m_ in gmenu]).count() == 0:
                         html = html + """<div data-kt-menu-placement="bottom-start" class="menu-item me-0 me-lg-2">
                               <!--begin:Menu link-->
                               <span class="menu-link py-3">
                               <span class="menu-title%s">%s</span>
                               <span class="menu-arrow d-lg-none"></span>
                               </span></div>\n"""%(text_primary,m.name)
                         continue
                   active = ''
                   if menu_active:
                       if m.url ==  menu_active.url:
                          active = 'here'

                   html = html + """<div data-kt-menu-trigger="{default: 'click', lg: 'hover'}" data-kt-menu-placement="bottom-start" class="menu-item %s menu-here-bg menu-lg-down-accordion me-0 me-lg-2">
                   <!--begin:Menu link-->
                   <span class="menu-link py-3">
                   <span class="menu-title%s">%s</span>
                   <span class="menu-arrow d-lg-none"></span>
                   </span>\n"""%(active,text_primary,m.name)

                   html = html + """<div class="menu-sub menu-sub-lg-down-accordion menu-sub-lg-dropdown p-0 w-100 w-lg-750px">
                   <!--begin:Dashboards menu-->
                   <div class="menu-state-bg menu-extended overflow-hidden overflow-lg-visible" data-kt-menu-dismiss="true">
                   <!--begin:Row-->
                   <div class="row">
                    <!--begin:Col-->
                    <div class="col-lg-8 mb-3 mb-lg-0 py-3 px-3 py-lg-6 px-lg-6">
                        <!--begin:Row-->
                        <div class="row">\n"""
            
            menu_child = []
            gmenu_terurut = Menu.objects.filter(id__in=[ menu_.id for menu_ in gmenu ],aktif=True).order_by('urutan','name') 
            for menu_child_item in gmenu_terurut:
                if menu_child_item.parent == m and menu_child_item.aktif:
                     if menu_child_item.as_beranda:
                         menu_child.insert(0,menu_child_item)
                     else:
                         menu_child.append(menu_child_item)
            menu_child_terurut = Menu.objects.filter(id__in=[ menu_.id for menu_ in menu_child ],aktif=True).order_by('urutan','name') 

            for mc in menu_child_terurut:
                #faw = mc.faw if mc.faw=null else "ki-element-11 text-primary"
                faw = "ki-element-11 text-primary"
                #faw = mc.faw if mc.faw is null else "ki-element-11 text-primary"
                if mc.description:
                    desc = mc.description
                else:
                    desc = mc.name
                if mc.isembed:
                     url = "{}?id={}".format(reverse('core:embed'),mc.id)
                else:
                     url = set_absolute_path(mc.url)
                target = ''
                if is_url_start_with_http(url):
                     target = " target='_blank' "

                if mc == menu_active:
                     text_style = "text-primary"
                else:
                     text_style = "text-gray-800"

                html = html + """<div class="col-lg-6 mb-3">
                                <!--begin:Menu item-->
                                <div class="menu-item p-0 m-0">
                                    <!--begin:Menu link-->
                                    <a href="%s" %s class="menu-link">
                                        <span class="menu-custom-icon d-flex flex-center flex-shrink-0 rounded w-40px h-40px me-3">
                                            <i class="ki-duotone %s text-primary fs-1">
                                                <span class="path1"></span>
                                                <span class="path2"></span>
                                                <span class="path3"></span>
                                                <span class="path4"></span>
                                            </i>
                                        </span>
                                        <span class="d-flex flex-column">
                                            <span class="fs-6 fw-bold %s">%s</span>
                                            <span class="fs-7 fw-semibold text-muted">%s</span>
                                        </span>
                                    </a>
                                    <!--end:Menu link-->
                                </div>
                                <!--end:Menu item-->
                    </div>\n"""%(url,target,mc.faw,text_style,mc.name,desc)
                
            html = html + "</div></div></div></div></div>\n"
            html = html + "</div>\n"
        html = html + "</div></div></div>\n"
    context['menu'] = html
    return context
show_menu_template_ng = get_template('core/menu_ng.html') 
register.inclusion_tag(show_menu_template_ng)(show_ng_menu)


def show_topmenu(path='',user=None):
    top_menu = []
    if user.is_superuser:
        top_menu = Menu.objects.filter(aktif=True,aplikasi__aktif=True,parent=None).order_by('urutan','name').prefetch_related()
    else:
        group_menu = GroupMenu.objects.filter(group__in=user.groups.all()).prefetch_related()
        for gm in group_menu:
            for m in gm.menu.all().filter(parent=None).exclude(Q(aplikasi__aktif=False)|Q(aktif=False)).order_by('urutan','name'):
                 if m in top_menu:
                     continue
                 else:
                     top_menu.append(m)
    top_menu_berurut = Menu.objects.filter(id__in=[ menu_.id for menu_ in top_menu ],aktif=True).order_by('urutan','name')
    top_menu = top_menu_berurut
    context = {}
    html = ''
    menu_active = None
    uri = []
    if path != '':
        id_embed = id_embed_from_url(path)
        if id_embed:
             menu_active = Menu.objects.filter(id=id_embed,aktif=True,aplikasi__aktif=True).first()
        else:
             menu_active = Menu.objects.filter(aktif=True,aplikasi__aktif=True).filter(Q(url__exact=path)|Q(url__exact=get_relative_path(path))).first()

    for tm in top_menu:
        if not menu_have_childs(tm):
             #continue
             target = ''
             if is_url_start_with_http(tm.url):
                         target = " target='_blank' "
             try: 
                 if tm == menu_active or tm == menu_active.parent or tm == menu_active.parent.parent or tm == menu_active.parent.parent.parent :
                     html = html + """<li class="nav-item"><a class="nav-link active" data-bs-toggle="" href="%s" %s>%s</a></li>\n"""%(set_absolute_path(tm.url),target,tm.name)
                 else:
                     html = html + """<li class="nav-item"><a class="nav-link" data-bs-toggle="" href="%s" %s>%s</a></li>\n"""%(set_absolute_path(tm.url),target,tm.name)
             except:
                     html = html + """<li class="nav-item"><a class="nav-link" data-bs-toggle="" href="%s" %s>%s</a></li>\n"""%(set_absolute_path(tm.url),target,tm.name)

        else:
            try:
                if tm == menu_active or tm == menu_active.parent or tm == menu_active.parent.parent or tm == menu_active.parent.parent.parent :
                     html = html + """<li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#kt_header_navs_tab_%s">%s</a></li>\n"""%(tm.id,tm.name)
                else:
                     html = html + """<li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#kt_header_navs_tab_%s">%s</a></li>\n"""%(tm.id,tm.name)
            except:
                html = html + """<li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#kt_header_navs_tab_%s">%s</a></li>\n"""%(tm.id,tm.name)
        
    context['topmenu'] = html
    return context
show_topmenu_template = get_template('core/topmenu.html')  
register.inclusion_tag(show_topmenu_template)(show_topmenu)

def show_appmenu(path='',user=None):
    gmenu = []
    if user :
        if user.is_superuser:
            gmenu = Menu.objects.all()
        else:
            try:
                gm = GroupMenu.objects.get(group=user.groups.all()[0])
                gmenu = gm.menu.all()
            except:
                #raise
                gmenu = []

    context = {}
    apps = Aplikasi.objects.filter(aktif=True).filter(as_modul=False).order_by('urutan')
   
    html = ''
    active = ''
    for app in apps:
        html = html + f"""<div class="col-6">
        <a href="{app.url}" target="_blank" class="d-flex flex-column flex-center h-100 p-6 bg-hover-light border-end border-bottom">
            <div class="symbol symbol-20px symbol-md-30px">
               <img src="{settings.MEDIA_URL}/{app.image}" alt="{app.name}"></img>
            </div>
            <span class="fs-7 fw-semibold text-gray-800 mb-0">{app.name}</span>
            <span class="fs-8 text-gray-400" style="text-align:center">{app.description}</span>
        </a>
        </div>\n"""
        context['appmenu'] = html
    return context
show_appmenu_template = get_template('core/appmenu.html')  
register.inclusion_tag(show_appmenu_template)(show_appmenu)

@register.filter
def format_rupiah(value):
    return "Rp{:,.0f}".format(value)
