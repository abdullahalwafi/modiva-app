from django.shortcuts import render, redirect
from django.views.generic import ListView,DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request,HttpResponseRedirect
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

#from .models import Pemda, Provinsi, Kecamatan, TahunPemda, TahunKecamatan, TahunDesa
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin
import logging

logger = logging.getLogger(__name__)

from modules.uman.decorators  import group_must_have_permission
from django.utils.decorators import method_decorator

