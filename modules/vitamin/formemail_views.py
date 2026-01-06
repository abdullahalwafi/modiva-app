from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q

from modules.landingpage.models import ContactMessage

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

from .forms import *

import pandas as pd
from django.http import HttpResponse

# ----------------referensi Vitamin--------------------

@method_decorator([group_must_have_permission], name='dispatch')
class ContactMessageListView(LoginRequiredMixin,PermissionRequiredMixin, ListView):
    model = ContactMessage
    paginate_by = 5
    permission_required = 'vitamin.view_contactmessage'
    def get_template_names(self):
        if self.request.htmx:
            return ["vitamin/formemail/formemail_list.html"] # The response HTML to inject into a list
        else:
            return ["vitamin/formemail/formemail.html"] # The actual form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["numlist"] = (int(self.request.GET.get("page",1)) - 1) * self.paginate_by
        context["q"] = self.request.GET.get("q",'')
        context["title"] = "Daftar Isi Form"
        return context
    
    def get_queryset(self):
        qs = self.model.objects.all()
        if self.request.GET.get("q",''):
              qs = self.model.objects.filter(
                 Q(puskesmas__icontains=self.request.GET.get("q",'')) | 
                 Q(email__icontains=self.request.GET.get("q",'')) |
                 Q(message__icontains=self.request.GET.get("q",'')) 
              )
        return qs.order_by('-id')
    

class ContactMessageUpdateView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = ContactMessage
    template_name = 'vitamin/formemail/formemail_edit.html'
    form_class = ContactMessageForm
    success_url = reverse_lazy('vitamin:contactmessage-list')
    permission_required = 'vitamin.change_contactmessage'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ubah Form Isi"
        return context

class ContactMessageDeleteView(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    model = ContactMessage
    template_name = 'vitamin/formemail/formemail_delete.html'
    success_url = reverse_lazy('vitamin:contactmessage-list')
    permission_required = 'vitamin.delete_contactmessage'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hapus Data"
        return context

class ContactMessageDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = ContactMessage
    template_name = 'vitamin/formemail/formemail_detail.html'
    success_url = reverse_lazy('vitamin:contactmessage-list')
    permission_required = 'vitamin.view_contactmessage'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #mp = MenuProduk.objects.filter(produk=self.model.objects.get(id=self.kwargs.get('pk'))).first()
        #context["menu_list"] = mp.menu.all().order_by('name')
        context["title"] = "Detail "
        print(context)
        return context
    
def get_notifications(request):
    notifications = ContactMessage.objects.filter(status=0).order_by('-timestamp')
    return render(request, 'include/modiva_navbar3.html', {'notifications': notifications})
    
