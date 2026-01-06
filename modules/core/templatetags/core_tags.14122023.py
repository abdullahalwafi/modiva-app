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


from modules.core.core_libs import format_rp_currency

@register.simple_tag
def to_rp(amount):
    return format_rp_currency(amount)

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

def get_user_menu(user):

    user_menu = []
    top_menu = []

    if user.is_superuser:
        top_menu = Menu.objects.filter(aktif=True,aplikasi__aktif=True,parent=None).order_by('urutan','name').prefetch_related()
        user_menu = Menu.objects.filter(aktif=True,aplikasi__aktif=True).exclude(parent=None).order_by('urutan','name').prefetch_related()

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
                       if m_ in user_menu:
                          continue
                       else:
                          user_menu.append(m_)
     
    menu_all = (top_menu,user_menu)  
    return menu_all

def get_active_menu(path):
    menu_active = None
    id_embed = None
    if path != '':
        id_embed = id_embed_from_url(path)
        if id_embed:
                  menu_active = Menu.objects.filter(id=id_embed,aktif=True,aplikasi__aktif=True).first()
        else:
             menu_active = Menu.objects.filter(aktif=True,aplikasi__aktif=True).filter(Q(url__exact=path)|Q(url__exact=get_relative_path(path))).first()
    return menu_active

def topmenu_html(tm,active=''):
    html = """<div class="tab-pane fade %s show" id="kt_header_navs_tab_%s">
              <!--begin::Menu wrapper-->
              <div class="header-menu flex-column align-items-stretch flex-lg-row">
               <!--begin::Menu-->
                    <div class="menu menu-rounded menu-column menu-lg-row menu-root-here-bg-desktop menu-active-bg menu-title-gray-700 menu-state-primary menu-arrow-gray-400 fw-semibold align-items-stretch flex-grow-1 px-2 px-lg-0" id="#kt_header_menu" data-kt-menu="true">\n"""%(active,tm.id)
    return html

def menu_item_with_child(menu,level='',active='',here='',is_sub=False):
    sub = ''
    if level == 1:
         pixel=225
    elif level == 2:
         pixel=250
    else:
         pixel=220
    if is_sub:
         sub = f"""<div class="menu-sub {here} menu-sub-lg-down-accordion menu-sub-lg-dropdown 
               px-lg-2 py-lg-4 w-lg-{pixel}px">\n
         """
    if menu.faw:
         icon_faw = """<span class="menu-icon">
                       <i class="%s fs-2">
                         <span class="path1"></span>
                         <span class="path2"></span>
                       </i>
                     </span>
         """%(menu.faw)
    else:
         icon_faw = ''
    if level == 2:
         html =  """
              <!--begin:Menu item-->
              <div data-kt-menu-trigger="{default: 'click', lg: 'hover'}" data-kt-menu-placement="right-start"
              class="menu-item %s menu-lg-down-accordion menu-sub-lg-down-indention me-0 me-lg-2">
                   <span class="menu-link %s py-3">
                     %s
                     <span class="menu-title">%s</span>
                     <span class="menu-arrow"></span>
                   </span>\n
         """%(here,active,icon_faw,menu.name)
    elif level == 1:
         html =  """<!--begin:Menu item-->
              <div data-kt-menu-trigger="{default: 'click', lg: 'hover'}" data-kt-menu-placement="bottom-start"
              class="menu-item %s menu-lg-down-accordion menu-sub-lg-down-indention me-0 me-lg-2">
              <!--begin:Menu link-->
              <span class="menu-link %s py-3">
               %s
               <span class="menu-title">%s</span>
               <span class="menu-arrow d-lg-none"></span>
              </span>
	      <!--end:Menu link-->\n
         """%(here,active,icon_faw,menu.name)
         
    else:
         html =  """<!--begin:Menu item-->
              <div data-kt-menu-trigger="{default: 'click', lg: 'hover'}" data-kt-menu-placement="right-start"
              class="menu-item %s menu-lg-down-accordion menu-sub-lg-down-indention me-0 me-lg-2">
              <!--begin:Menu link-->
              <span class="menu-link %s py-3">
               <span class="menu-title">%s</span>
               <span class="menu-arrow"></span>
              </span>
	      <!--end:Menu link-->\n
         """%(here,active,menu.name)
    return html+sub

def menu_item_without_child(menu,level='',url='',target='',active=''):
    if level == 1:
         html = f"""
           <!--begin:Menu item-->
             <div class="menu-item">
		<!--begin:Menu link-->
		<a class="menu-link {active} py-3" {target} href="{url}">
		   <span class="menu-title">{menu.name}</span>
		</a>
                <span class="menu-arrow d-lg-none"></span>
                <!--end:Menu link-->
             </div>
	   <!--end:Menu item-->\n
         """

    elif level == 2:
         html = f"""
           <!--begin:Menu item-->
             <div class="menu-item">
		<!--begin:Menu link-->
		<a class="menu-link {active} py-3" {target} href="{url}">
		   <span class="menu-bullet">
		     <span class="bullet bullet-dot"></span>
		   </span>
		   <span class="menu-title">{menu.name}</span>
		</a>
                <!--end:Menu link-->
             </div>
	   <!--end:Menu item-->\n
        """
    else:
        html = f"""
           <!--begin:Menu item-->
             <div class="menu-item">
		<!--begin:Menu link-->
		<a class="menu-link {active} py-3" {target} href="{url}">
		   <span class="menu-bullet">
		     <span class="bullet bullet-dot"></span>
		   </span>
		   <span class="menu-title">{menu.name}</span>
		</a>
                <!--end:Menu link-->
             </div>
	   <!--end:Menu item-->\n
        """
    return html

def get_child_menu(m,gmenu):
    menu_child = []
    gmenu_terurut = Menu.objects.filter(id__in=[ menu_.id for menu_ in gmenu ],aktif=True,parent=m).order_by('urutan','name') 
    for menu_child_item in gmenu_terurut:
        if menu_child_item.parent == m and menu_child_item.aktif:
             if menu_child_item.as_beranda:
                 menu_child.insert(0,menu_child_item)
             else:
                 menu_child.append(menu_child_item)

    menu_child_terurut = Menu.objects.filter(id__in=[ menu_.id for menu_ in menu_child ],aktif=True,parent=m).order_by('urutan','name') 
    return menu_child_terurut

def get_active_attrs(mc,menu_active):

    text_style = ""
    active = ''
    text_primary = ""
    target = ""
    url = ""
    here = ""
    attrs = None
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
       text_primary = " text-primary"
       here = 'here'
       active = 'active'
    else:
       try:
           if mc == menu_active.parent:
              text_style = "text-primary"
              text_primary = " text-primary"
              here = 'here'
              active = 'active'
           elif mc == menu_active.parent.parent:
              text_style = "text-primary"
              text_primary = " text-primary"
              here = 'here'
              active = 'active'
           elif mc == menu_active.parent.parent.parent:
              text_style = "text-primary"
              text_primary = " text-primary"
              here = 'here'
              active = 'active'
           elif mc == menu_active.parent.parent.parent.parent:
              text_style = "text-primary"
              text_primary = " text-primary"
              here = 'here'
              active = 'active'
           elif mc == menu_active.parent.parent.parent.parent.parent:
              text_style = "text-primary"
              text_primary = " text-primary"
              here = 'here'
              active = 'active'
           
           else:
              text_style = "text-gray-800"
              text_primary = ""
              here = ''
              active = ''
       except:
              text_style = ""
              text_primary = ""
              here = ''
              active = ''
    attrs = (url,target,active,here,text_primary,text_style)
    return attrs

def show_ng_menu(path='',user=None):
    context = {}
    html = ''
    top_menu,gmenu = get_user_menu(user)
    menu_active = get_active_menu(path)
    for tm in top_menu:
        url,target,active,here,text_primary,text_style = get_active_attrs(tm,menu_active)
        #---------------- Begin - Top Menu ------------------------
        html = html + topmenu_html(tm,active)
        #---------------- End - Top Menu ------------------------
        for m in Menu.objects.filter(parent=tm,id__in=[mn.id for mn in gmenu]).order_by('urutan','name'):
            url,target,active,here,text_primary,text_style = get_active_attrs(m,menu_active)
            menu_child = get_child_menu(m,gmenu) 
               
            if menu_child:
                 html = html + menu_item_with_child(m,1,active,here,True)
            else:
                 html = html + menu_item_without_child(m,1,url,target,active)
                 continue
            for mc in menu_child:
                 url,target,active,here,text_primary,text_style = get_active_attrs(mc,menu_active)
                 menu_child_level2 = get_child_menu(mc,gmenu) 
                 if  menu_child_level2:
                      html = html + menu_item_with_child(mc,2,active,here,True)
                 else:
                      html = html + menu_item_without_child(mc,2,url,target,active)
                      continue

                 for mc2 in menu_child_level2:
                      url,target,active,here,text_primary,text_style = get_active_attrs(mc2,menu_active)
                      menu_child_level3 = get_child_menu(mc2,gmenu) 
                      if  menu_child_level3:                   
                           html = html + menu_item_with_child(mc2,2,active,here,True)
                      else:
                           html = html + menu_item_without_child(mc2,2,url,target,active)
                           continue

                      for mc3 in menu_child_level3:
                           url,target,active,here,text_primary,text_style = get_active_attrs(mc3,menu_active)
                           menu_child_level4 = get_child_menu(mc3,gmenu) 
                           if  menu_child_level4:
                                 html = html + menu_item_with_child(mc3,2,active,here,True)
                           else:
                                 html = html + menu_item_without_child(mc3,2,url,target,active)
                                 continue
                           for mc4 in menu_child_level4:
                                 url,target,active,here,text_primary,text_style = get_active_attrs(mc4,menu_active)
                                 menu_child_level5 = get_child_menu(mc4,gmenu) 
                                 if  menu_child_level5:
                                       html = html + menu_item_with_child(mc4,2,active,here,False)
                                 else:
                                       html = html + menu_item_without_child(mc4,2,url,target,active)
                                       continue
                                 for mc5 in menu_child_level5:
                                       url,target,active,here,text_primary,text_style = get_active_attrs(mc5,menu_active)
                                       html = html + menu_item_without_child(mc5,2,url,target,active)
                                 html = html + "</div>\n"
                           html = html + "</div></div>\n"
                      html = html + "</div></div>\n"
                 html = html + "</div></div>\n"
            html = html + "</div></div>\n"
        html = html + "</div></div></div>\n"
    html = html + "</div></div></div>\n"
    context['menu'] = html
    return context
show_menu_template_ng = get_template('core/menu_ng.html') 
register.inclusion_tag(show_menu_template_ng)(show_ng_menu)


def show_topmenu(path='',user=None):
    top_menu = []
    top_menu,gmenu = get_user_menu(user)
    menu_active = get_active_menu(path)
    top_menu_berurut = Menu.objects.filter(id__in=[ menu_.id for menu_ in top_menu ],aktif=True).order_by('urutan','name')
    top_menu = top_menu_berurut
    context = {}
    html = ''
    for tm in top_menu:
        url,target,active,here,text_primary,text_style = get_active_attrs(tm,menu_active)
        if not menu_have_childs(tm):
             html = html + """<li class="nav-item"><a class="nav-link %s" data-bs-toggle="" href="%s" %s>%s</a></li>\n"""%(active,set_absolute_path(tm.url),target,tm.name)
        else:
            html = html + """<li class="nav-item"><a class="nav-link %s" data-bs-toggle="tab" href="#kt_header_navs_tab_%s">%s</a></li>\n"""%(active,tm.id,tm.name)
        
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
