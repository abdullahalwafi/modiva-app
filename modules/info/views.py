from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from modules.core.core_libs import *
from modules.uman.decorators  import group_must_have_permission
from django.contrib.auth.decorators import login_required

# Create your views here.
@group_must_have_permission
@login_required
def index(request):
    context = {}
    context['title'] = 'Index'
    return render(request, 'info/index.html', context)

