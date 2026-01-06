from django.shortcuts import render, redirect, reverse
# Create your views here.
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import request, HttpResponseRedirect
from django.conf import settings
import requests
from requests.auth import HTTPBasicAuth
from django.contrib import messages
from datetime import datetime
from django.utils.decorators import method_decorator
from modules.uman.decorators import *
import logging
from modules.uman.models import AppConfig

logger = logging.getLogger(__name__)


def tableuIframeUrl():
    coreconfig = AppConfig.objects.filter(
        namespace='core')
    config = {cfg.key: cfg.value for cfg in coreconfig}
    TABLEU_SITE_URL = config['tableu_site_url']
    TABLEU_TRUSTED_URL = TABLEU_SITE_URL + '/trusted'
    TABLEU_USER = config['tableu_username']
    TABLEU_PASS = config['tableu_password']
    TARGET_SITE = config['tableu_target_site']
    iframeurl = ''
    data = {"username": TABLEU_USER, "target_site": TARGET_SITE}
    session = requests.Session()
    req = session.post(TABLEU_TRUSTED_URL, data=data)
    if req.status_code == 200:
        if req.text != '-1':
            ticketID = req.text
            iframeurl = TABLEU_TRUSTED_URL + \
                f'/{ticketID}/t/DJPK/views/NEWAIFA_Publish2/Home_Dark'
        else:
            print("Tableau Server could not issue trusted Auth...")
    return iframeurl


@group_must_have_permission
def tableu_embed(request):
    template_name = 'core/embed/tableu.html'
    title = 'Tableu page'
    data = {'page_title': title, 'url': tableuIframeUrl()}
    return render(request, template_name, context=data)
