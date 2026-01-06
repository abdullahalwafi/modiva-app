from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings
from defender.decorators import watch_login
from allauth.socialaccount.models import SocialAccount
import json
import redis
import requests
from datetime import timedelta
from django.db import transaction


from modules.core.core_libs import *
from modules.uman.decorators  import group_must_have_permission
from .models import Menu,GroupAplikasi,Aplikasi,UserDetail, GroupMenu
#from .models import Pemda, Menu,GroupAplikasi,Aplikasi,UserDetail, GroupMenu, UserRegistration

from .forms import LoginForm,UpdateFotoProfilForm,UserProfileUpdateForm
from allauth.socialaccount.models import SocialAccount
#redis_client = redis.StrictRedis(host='172.17.0.4', port=6379, db=1)
#def publish_data_on_redis(json_data, channel_name):
#    redis_client.publish(channel_name, json.dumps(json_data))
r = redis_connection()
channel = 'sikd:uman:notifications'

def nopage(request):
    context = {}
    context['title'] = 'Warning' 
    #context['message'] = 'No menu assigned to your account'
    template_name = 'uman/nopage.html'
    #print('#### ',UserPegawai(request).kd_jabatan.nm_jabatan,'##### ', request.user.pegawai.kd_unit.nm_unit)
    if request.htmx:
         template_name = 'uman/nopage_partial.html'
    return render(request,template_name, context)


def beranda(request):
    menu = None
    gmenu = None
    url = reverse('uman:nopage')
    if request.user.is_authenticated:
        if request.user.is_superuser:
           menu = Menu.objects.filter(aktif=True,as_beranda=True,aplikasi__aktif=True).exclude(url=None).order_by('aplikasi__urutan','urutan','-as_beranda','name').first()
           if menu:
               if menu.isembed:
                     url = "{}?id={}".format(reverse('core:embed'),menu.id)
                     return set_absolute_path(url)
               return set_absolute_path(menu.url) 
           else:
               menu = Menu.objects.filter(aktif=True,aplikasi__aktif=True).order_by('aplikasi__urutan','urutan','name').exclude(url=None).first()
               if not menu:
                   messages.error(request,'Anda tidak memiliki otoritas')
                   return reverse('uman:nopage')
               if menu.isembed:
                     url = "{}?id={}".format(reverse('core:embed'),menu.id)
                     return set_absolute_path(url)
               return set_absolute_path(menu.url)
        else:
               gmenu = GroupMenu.objects.filter(group__in=request.user.groups.all())
               ids_menu = []
               menu_beranda = None
               for gm in gmenu:
                     for m in gm.menu.all():
                         if m.id in ids_menu:
                              continue
                         else:
                            ids_menu.append(m.id)
               if not ids_menu:
                     url = reverse('uman:nopage')
                     messages.error(request,'Anda tidak memiliki otoritas')
                     return url
                      
               menu = Menu.objects.filter(id__in=ids_menu,aktif=True,as_beranda=True,aplikasi__aktif=True).exclude(url=None).order_by('aplikasi__urutan','urutan','as_beranda','name').first()
               if menu:
                     if menu.isembed:
                         url = "{}?id={}".format(reverse('core:embed'),menu.id)
                         return set_absolute_path(url)
                     return set_absolute_path(menu.url)
               else:
                     menu = Menu.objects.filter(id__in=ids_menu,aktif=True,aplikasi__aktif=True).exclude(url=None).order_by('aplikasi__urutan','urutan','as_beranda','name').first()
                     if menu:
                         if menu.isembed:
                             url = "{}?id={}".format(reverse('core:embed'),menu.id)
                             return set_absolute_path(url)
                         else:
                             return set_absolute_path(menu.url)
                     else:
                         url = reverse('uman:nopage')
                         messages.error(request,'Anda tidak memiliki otoritas')
                         return url
    return ''

@csrf_protect
@watch_login(status_code=302)
def login_view(request):
    form = LoginForm(request.POST or None)
    apps = Aplikasi.objects.filter(aktif=True, as_modul=False).order_by('urutan','name')

    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                data = {'event_tye':'login','user':user.username}
                publish_data_on_redis(r,data,channel)
                if request.GET:
                    url = request.GET['next']
                if request.POST:
                    #url = reverse('uman:home')
                    url = beranda(request)
                    if url:
                        return redirect(url)
                    else:
                        return redirect(reverse('uman:nopage'))
            else:
                msg = 'Username dan/atau Password Anda Salah'
                messages.error(request,msg)
                # Jangan diubah, ini agar django-defender bisa memblok upaya brute foarce
                # karena django-defender membedakan login berhasil dan bukan dari status code
                # kalau login berhasil maka aplikasi harus redirect (status=302) bukan
                # rendering template, karena rendering defaultnya dianggap login gagal 
                return render(request, 'uman/login.html', {'form': form,'apps':apps})
                #return redirect(reverse('uman:login'))
        else:
            msg = 'Gagal memvalidasi isian form'
            messages.error(request,msg)
            return render(request, 'uman/login.html', {'form': form,'apps':apps})
            #return redirect(reverse('uman:login'))
    else:
        url_beranda =  beranda(request)
        if url_beranda:
            return redirect(url_beranda)
        #messages.info(request,'!!!! %s'%url_beranda)
        return render(request, 'uman/login.html', {'form': form,'apps':apps})


def logout_view(request):
    logout(request)
    return redirect(reverse('uman:login'))

@group_must_have_permission
@login_required
def home(request):
    context = {}
    context['aplikasis']=Aplikasi.objects.filter(aktif=True).order_by('-urutan')
    context['grupapp']=GroupAplikasi.objects.filter(aktif=True).order_by('-urutan')
    
    return render(request, 'uman/home.html', context)


def testingrequest(request):
    data = '<h1>' + request.path + ' by ' + request.user.username + '</h1>'
    return HttpResponse(data)


#def test_manajemen_user(request):
#    context = {}
#    context['model'] = request.user.get_all_permissions()
#    context['pemda'] = Pemda.objects.prefetch_related('name__pemda').filter(
#        Q(group_pemda__group__in=request.user.groups.all())
#        | Q(pemda__user=request.user)
#        ).distinct()

#    return render(request, 'uman/test_manajemen_user.html', context)

#added by boypyt
@login_required
def change_password(request):
    try:
         SocialAccount.objects.get(user=request.user)
         messages.warning(request, 'Warning: perubahan password harus dilakukan pada SSO Server Kemenkeu  ')
         #return redirect(request.META['HTTP_REFERER'])
         return redirect(reverse('uman:profile-account'))
    except:
         pass
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect(reverse('uman:profile-account'))
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    if request.htmx:
        return render(request, 'uman/change_password_partial.html', {
             'form': form
        })
    else:
        return render(request, 'uman/change_password.html', {
             'form': form
        })


@csrf_protect
@login_required
def profile_account(request):
    if request.htmx:
        #return render(request, 'uman/profile_account_partial.html')
        return render(request, 'uman/partial_profile_account.html')
    else:
        return render(request, 'uman/profile_account.html')

@login_required
def update_foto_profile(request,pk):
    if request.htmx and request.method == 'POST':
        form_data = request.POST.dict()
        return render(request, 'uman/update_foto_profile.html')
    else:
        return render(request, 'uman/profile_account.html')

class UpdateFotoProfilView(LoginRequiredMixin,UpdateView):
    model = UserDetail
    template_name = 'uman/update_foto_profile.html'
    form_class = UpdateFotoProfilForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        self.success_url = reverse('uman:update-foto-profile',kwargs={'pk':obj.id})
        return super(UpdateFotoProfilView, self).form_valid(form)

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST.get('email','')
       
        if not email:
            messages.error(request, '!!Please fill email account')
            return redirect(reverse('uman:forgot-password'))

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('uman/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect(reverse('uman:login'))
        else:
            messages.error(request, 'Account does not exist!')
            return redirect(reverse('uman:forgot-password'))
    return render(request, 'uman/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect(reverse('uman:reset-password'))
    else:
        messages.error(request, 'This link has been expired!')
        return redirect(reverse('uman:login'))

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = User.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect(reverse('uman:login'))
        else:
            messages.error(request, 'Password do not match!')
            return redirect(reverse('uman:reset-password'))
    else:
        return render(request, 'uman/resetPassword.html')

def custom_permission_denied_view(request, exception=None):
    messages.error(request, 'Permission Denied !!!')
    response = render(request, "errors/403.html", {})
    response.status_code = 403
    return  response

@csrf_protect
@login_required
def update_user_profile(request):
    try:
            object = UserDetail.objects.get(user=request.user)
    except:
            messages.warning(request,'Tidak ada data pengguna')
            return redirect(reverse('uman:profile-account'))

    if request.htmx:
        template_name = 'uman/update_user_profile_partial.html'
    else:
        template_name = 'uman/update_user_profile.html'
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST,instance=object)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                u = User.objects.get(id=obj.user.id)
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                email = form.cleaned_data.get('email')
                u.first_name = first_name
                u.last_name = last_name
                u.email = email
                obj.save()
                u.save()
                messages.success(request,'Update profile berhasil dilakukan')
            except:
                messages.warning(request,'Update profile gagal dilakukan')
        else:
            messages.warning(request,'Update profile gagal dilakukan')
        return redirect(reverse('uman:profile-account'))
    else:
        form = UserProfileUpdateForm(instance=object)
        return render(request,template_name,{'title':'Edit User Profile','form':form})
   
