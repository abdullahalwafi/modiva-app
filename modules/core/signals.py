from django.db.models import signals
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from django.db.models import Q
import os


import json
from .core_libs import redis_connection, publish_data_on_redis

from datetime import datetime
from django.forms.models import model_to_dict
from django.conf import settings

r = redis_connection()
channel = 'sikd:core:data'
