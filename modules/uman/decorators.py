from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from .models import Menu,GroupMenu

import functools
from django.shortcuts import redirect,reverse
from django.contrib import messages
from django.http import HttpResponseForbidden 

from django.conf import settings
from django.db.models import Q
from modules.core.core_libs import root_url, is_absolute_path, set_absolute_path, id_embed_from_url, get_relative_path

def is_members(user,groups):
    if user.is_superuser:
        return user
    return user.groups.filter(name__in=groups)

def is_member_of(user,group):
    if user.is_superuser:
        return user
    return user.groups.filter(name=group)

def all_user_menu(user):
    all_menu = []
    user_groups = user.groups.all()
    group_menus = GroupMenu.objects.filter(group__in=user_groups)
    for gm in group_menus:
          for menu in gm.menu.all():
              all_menu.append(menu)
    return all_menu

def url_in_menu(current_url):
    id_embed = id_embed_from_url(current_url)
    if id_embed:
        menu = Menu.objects.filter(id=id_embed).order_by('urutan','name').first()
    else:
        menu = Menu.objects.filter( Q(url__exact=current_url)|Q(url__exact=get_relative_path(current_url))).order_by('urutan','name').first()
    #print('#########%s , %s , MENU : %s'%(current_url,get_relative_path(current_url),menu))
    if menu:
        return menu
    else:
        return None

def user_have_menu(current_url,user):
    user_menu = all_user_menu(user)
    menu_id = [ m.id for m in user_menu ]
    id_embed = id_embed_from_url(current_url)
    if id_embed:
        menu = Menu.objects.filter(id=id_embed,id__in=menu_id).order_by('urutan','name').first()
    else:
        menu = Menu.objects.filter(id__in=menu_id).filter( Q(url__exact=current_url)|Q(url__exact=get_relative_path(current_url))).order_by('urutan','name').first()
    if menu:
        return True
    else:
        return False

    
def group_have_permission_menu(user,req):
    current_url = req.get_full_path()
    #print(current_url)
    if user.is_superuser:
        if url_in_menu(current_url):
             if url_in_menu(current_url).aplikasi.aktif and url_in_menu(current_url).aktif:
                  return True
             else:
                  return False
        return True
    if not url_in_menu(current_url):
         return True
    else:
         if url_in_menu(current_url) and user_have_menu(current_url,user):
              #print('>>>>> ',current_url)
              if url_in_menu(current_url).aplikasi.aktif and url_in_menu(current_url).aktif:
                   return True
              else:
                   return False
    return False

#def groups_required(groups=[],function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='/'):
def groups_required(groups=[],function=None, redirect_field_name='', login_url='/'):
    '''
    Decorator for views that checks that the logged in user is a member of on or more group,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and is_members(u,groups),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def group_must_have_permission(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Session telah expire atau Anda harus login dahulu")
            return redirect(reverse('uman:login'))
        if request.user.is_active and group_have_permission_menu(request.user,request):
            return view_func(request,*args, **kwargs)
        messages.warning(request, "Maaf Anda tidak memiliki otoritas mengakses halaman ini ")
        #print("You need to be logged out")
        #return HttpResponseForbidden()
        return redirect(reverse('uman:nopage'))
    return wrapper

#def pemda_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='/'):
def pemda_required(function=None, redirect_field_name='', login_url='/'):
    '''
    Decorator for views that checks that the logged in user is a pemda group,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and is_member_of(u,'pemda'),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

#def djpk_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='/'):
def djpk_required(function=None, redirect_field_name='', login_url='/'):
    '''
    Decorator for views that checks that the logged in user is a djpk group,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and is_member_of(u,'djpk'),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

#def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='/'):
def admin_required(function=None, redirect_field_name='', login_url='/'):
    '''
    Decorator for views that checks that the logged in user is a admin group,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and is_member_of(u,'admin'),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def admin_pemda_permission(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Session telah expire atau Anda harus login dahulu")
            return redirect(reverse('uman:login'))
        try:
            if request.user.is_superuser:
                 return view_func(request,*args, **kwargs)
            if request.user.is_active and request.user.userdetail.as_admin == 'pemda':
                 return view_func(request,*args, **kwargs)
            else:
                messages.warning(request, "Maaf Anda tidak memiliki otoritas mengakses halaman ini (1) ")
        except:
            raise
            if request.user.is_superuser:
                 return view_func(request,*args, **kwargs)
            else:
                messages.warning(request, "Maaf Anda tidak memiliki otoritas mengakses halaman ini (2) ")
        #print("You need to be logged out")
        #return HttpResponseForbidden()
        return redirect(reverse('uman:nopage'))
    return wrapper
