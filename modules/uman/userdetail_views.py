from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request, HttpResponseRedirect
from django.db.models import Q
from django.contrib.auth.models import User, Group

from .models import UserDetail
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin
from modules.core.core_libs import *
from django.contrib import messages
from django.db import transaction


from modules.uman.decorators import group_must_have_permission
from django.utils.decorators import method_decorator
from allauth.socialaccount.models import SocialAccount
from datetime import datetime
from libs.sikd_utils import namedtuplefetchall,  dictfetchall
from django.db import connection
import logging

logger = logging.getLogger(__name__)


# ----------------userkecamatan--------------------
# @group_must_have_permission <-- kalau funvtion based


@method_decorator([group_must_have_permission], name='dispatch')
class UserDetailListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = UserDetail
    permission_required = 'uman.view_userdetail'
    #paginate_by = 50

    def get_template_names(self):
        if self.request.htmx:
            # The response HTML to inject into a list
            return ["uman/userdetail/userdetail_list.html"]
        else:
            return ["uman/userdetail/userdetail.html"]  # The actual form

    def get_queryset(self):
        criteria = ""
        if self.request.GET.get('q',''):
             q = self.request.GET.get('q')
             criteria = f" WHERE a.username ilike '%{q}%' OR a.first_name ilike '%{q}%'"
             criteria = criteria + f" OR a.last_name ilike '%{q}%' OR a.email ilike '%{q}%'"
             #criteria = criteria + f" OR u.nip ilike '%{q}%' OR p.nm_pemda ilike '%{q}%' OR u.kode_satker ilike '%{q}%' "
        #logger.info(f'{datetime.today()} - INFO - [uman.userdetaila_views.UserDetailListView] - Start Running queryset')
        #sql = f"select u.id,u.user_id,p.nm_pemda,u.kode_satker,no_wa,no_hp,u.nip,u.foto_profil,a.username,a.is_active,a.email,a.first_name,a.last_name from uman_userdetail u left join pemda p on p.kd_satker=u.kode_satker inner join auth_user a on a.id=u.user_id {criteria} order by a.username"
        sql = f"select u.id,u.user_id,no_wa,no_hp,u.nip,u.foto_profil,a.username,a.is_active,a.email,a.first_name,a.last_name from uman_userdetail u inner join auth_user a on a.id=u.user_id {criteria} order by a.username"
        
        with connection.cursor() as cursor:
             cursor.execute(sql)
             return  dictfetchall(cursor)
             
        #qs = self.model.objects.raw(sql)
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Daftar User Detail"
        #context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * self.paginate_by
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) 
        context["q"] = self.request.GET.get("q",'')
        return context

class UserDetailCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = UserDetail
    template_name = 'uman/userdetail/userdetail_form.html'
    success_url = reverse_lazy('uman:userdetail-list')
    # permission_required = 'uman.add_userkecamatan'
    permission_required = 'uman.add_userdetail'
    form_class = UserDetailCreateForm

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(UserDetailCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    # def form_invalid(self, form):
    #    """If the form is invalid, render the invalid form."""
    #    return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save(commit=False)
        #print('##### ', self.object)
        self.object.save()
        messages.success(self.request, 'User was created successfully!')
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        self.object = None
        email = None
        form = self.get_form()
        username = request.POST.get('user')
        password = request.POST.get('password')
        is_superuser = request.POST.get('is_superuser', False)
        if is_superuser:
            is_superuser = True
        is_active = request.POST.get('is_active', False)
        if is_active:
            is_active = True
        u = User(username=username, last_name=username, email='{}@gmail.com'.format(
            username), is_staff=False, is_superuser=is_superuser, is_active=is_active)
        u.set_password(password)
        try:
            email = request.POST.get('email')
            if email:
                u.email = email
            u.save()
        except:
            return self.form_invalid(form)
        # grp = Group.objects.get(name='pemda')
        # grp.user_set.add(u)
        groups = request.POST.getlist('group')
        # print('#### GROUPS: ',groups)
        user_groups = Group.objects.filter(pk__in=[int(idx) for idx in groups])
        if user_groups:
            u.groups.set(user_groups)

        # self.request.POST.update({'user':u})
        # if form.is_valid():
        if u:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create User Detail"
        return context


class UserDetailUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = UserDetail
    template_name = 'uman/userdetail/userdetail_edit.html'
    success_url = reverse_lazy('uman:userdetail-list')
    permission_required = 'uman.change_userdetail'
    form_class = UserDetailUpdateForm

    def get_template_names(self):
        if self.request.htmx:
            # The response HTML to inject into a list
            return ["uman/userdetail/userdetail_edit_partial.html"]
        else:
            return ["uman/userdetail/userdetail_edit.html"]  # The actual form

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(UserDetailUpdateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        groups = form.cleaned_data.get('group')
        email = form.cleaned_data.get('email')
        is_superuser = form.cleaned_data.get('is_superuser')
        if is_superuser:
            is_superuser = True
        else:
            is_superuser = False
        is_active = form.cleaned_data.get('is_active')
        if is_active:
            is_active = True
        else:
            is_active = False
        user_groups = Group.objects.filter(pk__in=[int(idx) for idx in groups])
        self.object = form.save(commit=False)
        u = User.objects.get(id=self.object.user.id)
        u.is_active = is_active
        u.is_superuser = is_superuser
        if user_groups:
            self.object.user.groups.set(user_groups)
        if email:
            u.email = email
        u.save()
        self.object.save()
        messages.success(
            self.request, 'User %s was updated successfully!' % self.object.user.username)
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah User Detail"
        return context


class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = UserDetail
    template_name = 'uman/userdetail/userdetail_detail.html'
    success_url = reverse_lazy('uman:userdetail-list')
    permission_required = 'uman.view_userdetail'

    def get_object(self, queryset=None):
        #qs = UserDetail.objects.raw("select u.id,u.user_id,p.nm_pemda,u.kode_satker,u.kd_kementerian,p.kd_pemda_dagri,no_wa,no_hp,u.foto_profil,a.username,a.is_active,a.email from uman_userdetail u left join pemda p on p.kd_satker=u.kode_satker  inner join auth_user a on a.id=u.user_id where u.id={} ".format(self.kwargs.get('pk')))
        qs = UserDetail.objects.raw("select u.id,u.user_id,no_wa,no_hp,u.foto_profil,a.username,a.is_active,a.email from uman_userdetail u inner join auth_user a on a.id=u.user_id where u.id={} ".format(self.kwargs.get('pk')))
        if qs:
            return qs[0]
        else:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "User Detail"
        #context['kementerian'] = Kementerian.objects.filter(
         #   kode=self.get_object().kd_kementerian).first()
        return context


class UserDetailDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = UserDetail
    template_name = 'uman/userdetail/userdetail_delete.html'
    success_url = reverse_lazy('uman:userdetail-list')
    permission_required = 'uman.delete_userdetail'

    def form_valid(self, form):
        # If the form is valid, save the associated model
        # self.object = form.save(commit=False)
        # self.object.user.active = False
        self.object.user.delete()
        messages.success(self.request, 'User was deleted successfully!')
        return HttpResponseRedirect(self.get_success_url())
    """
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        #user = User.objects.get(pk=self.object.user.id)
        #print('USER###',user.username)
        self.object.user.delete()
        #user.groups.clear()
        #user.delete()
        messages.success(self.request, 'User was deleted successfully!')
        return HttpResponseRedirect(success_url)
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus User Detail"
        return context


@login_required
def statusUserDetail(request, pk):
    user_ = User.objects.filter(id=pk).first()
    active = request.GET.get('active', '')
    user_.is_active = False
    if active:
        user_.is_active = True
    user_.save()
    return redirect(reverse_lazy('uman:userdetail-list'))


@login_required
def ubahPasswordUserDetail(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'You are not authorize !! .')
        return redirect(reverse_lazy('uman:nopage'))

    template_name = 'uman/userdetail/userdetail_change_password.html'
    if request.htmx:
        template_name = 'uman/userdetail/userdetail_change_password_partial.html'
    form = UserDetailPasswordForm(request.POST or None)
    userdetail = UserDetail.objects.get(id=pk)
    if request.method == 'POST':
        if form.is_valid():
            password = form.cleaned_data['password']
            password2 = form.cleaned_data['password2']
            if password == password2:
                userdetail.user.set_password(password)
                userdetail.user.save()
                messages.success(request, 'Password was successfully updated!')
                return redirect(reverse_lazy('uman:userdetail-list'))
            else:
                messages.success(request, "Password doesn't Matched!")
        else:
            messages.error(request, 'Please correct the error below.')

    return render(request, template_name, {'form': form, 'pk': pk, 'object': userdetail, 'title': 'Ubah Password'})
