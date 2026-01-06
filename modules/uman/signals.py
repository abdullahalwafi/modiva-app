from django.db.models import signals
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import GroupAplikasi,Aplikasi,GroupMenu,Menu,EmbedMenu,UserDetail
from django.db.models import Q
import os


import json
from modules.core.core_libs import redis_connection, publish_data_on_redis

from datetime import datetime
from django.forms.models import model_to_dict
from django.conf import settings

r = redis_connection()
channel = 'sikd:uman:data'

@receiver(post_save, sender=GroupAplikasi)
def post_add_group_aplikasi(sender, instance, created, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       if created:
          #Add new data
          data['event_type'] = 'group_aplikasi.add'
       else:
          #Update data
          data['event_type'] = 'group_aplikasi.update'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data,channel)
    except:
       pass
           
@receiver(post_delete, sender=GroupAplikasi)
def post_delete_group_aplikasi(sender, instance, *args, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       data['event_type'] = 'group_aplikasi.delete'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass

@receiver(post_save, sender=Aplikasi)
def post_add_aplikasi(sender, instance, created, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       if created:
          #Add new data
          data['event_type'] = 'aplikasi.add'
       else:
          #Update data
          data['event_type'] = 'aplikasi.update'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass

@receiver(post_delete, sender=Aplikasi)
def post_delete_aplikasi(sender, instance, *args, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       data['event_type'] = 'aplikasi.delete'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass

@receiver(post_save, sender=GroupMenu)
def post_add_group_menu(sender, instance, created, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       if created:
          #Add new data
          data['event_type'] = 'group_menu.add'
       else:
          #Update data
          data['event_type'] = 'group_menu.update'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass
@receiver(post_delete, sender=GroupMenu)
def post_delete_group_menu(sender, instance, *args, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       data['event_type'] = 'group_menu.delete'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass

@receiver(post_save, sender=Menu)
def post_add_menu(sender, instance, created, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       if created:
          #Add new data
          data['event_type'] = 'menu.add'
       else:
          #Update data
          data['event_type'] = 'menu.update'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass
@receiver(post_delete, sender=Menu)
def post_delete_menu(sender, instance, *args, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       data['event_type'] = 'menu.delete'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass

@receiver(post_save, sender=EmbedMenu)
def post_add_embed_menu(sender, instance, created, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       if created:
          #Add new data
          data['event_type'] = 'embed_menu.add'
       else:
          #Update data
          data['event_type'] = 'embed_menu.update'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass
@receiver(post_delete, sender=EmbedMenu)
def post_delete_embed_menu(sender, instance, *args, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       data['event_type'] = 'embed_menu.delete'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass

@receiver(post_save, sender=UserDetail)
def post_add_user_detail(sender, instance, created, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       if created:
          #Add new data
          data['event_type'] = 'user_detail.add'
       else:
          #Update data
          data['event_type'] = 'user_detail.update'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       #raise
       pass
@receiver(post_delete, sender=UserDetail)
def post_delete_user_detail(sender, instance, *args, **kwargs):
    try:
       model_data = model_to_dict(instance)
       data = dict()
       data['event_type'] = 'user_detail.delete'
       data['datetime'] = str(datetime.now())
       data['data'] = model_data
       publish_data_on_redis(r,data, channel)
    except:
       pass

