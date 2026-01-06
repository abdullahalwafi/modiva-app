from .models import LogMenu
from modules.uman.models import Menu
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse_lazy
from modules.core.core_libs import root_url
from modules.core.templatetags.core_tags import get_active_menu
from django.conf import settings
#from modules.uman.decorators import *

class MenuAccessLogsMiddleware(object):

    def __init__(self, get_response=None):
        self.get_response = get_response
        # One-time configuration and initialization.
    def __call__(self, request):
        access_logs_data = dict()
    
        response = self.get_response(request)
        try:
            if not settings.MYTASK_LOGGING_ENABLED:
                   return response
        except:
            pass
        # get the request path
        current_url = request.get_full_path()
        current_url_rel = current_url.replace(root_url(),'')
        if current_url == reverse_lazy('mytask:log-aktifitas') or current_url_rel == reverse_lazy('mytask:log-aktifitas'):
             return response
        menu_ = get_active_menu(current_url,request.user)
        #menu_ = Menu.objects.filter( Q(url__exact=current_url) | Q(url__exact=current_url.split('?')[0]) | Q(url__exact=current_url_rel) | Q(url__exact=current_url_rel.split('?')[0])).first()
        if menu_ :
             access_logs_data["menu"] = menu_
        else:
            return response

        data = dict()
        #data["get"] = dict(request.GET.copy())
        #data['post'] = dict(request.POST.copy())
        # get the client's IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        data["ip_address"] = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        data["method"] = request.method
        data["referrer"] = request.META.get('HTTP_REFERER',None)
        data["datetime"] = str(timezone.now())
        data["url_request"] = current_url

        # remove password form post data for security reasons
        #keys_to_remove = ["password", "csrfmiddlewaretoken"]
        #for key in keys_to_remove:
        #    data["post"].pop(key, None)

        access_logs_data["data"] = data
        #access_logs_data["user_id"] = request.user.id
        access_logs_data["created_by"] = request.user.id
        access_logs_data["updated_by"] = request.user.id

        try:
            LogMenu(**access_logs_data).save()
            
        except Exception as e:
            #raise e
            pass 

        return response
