from django.db.models import signals
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import LogMenu
from django.db.models import Q
from datetime import datetime

@receiver(post_save, sender=LogMenu)
def post_add_logmenu(sender, instance, created, **kwargs):
    try:
       if created:
           lm = LogMenu.objects.filter(pk__lt=instance.pk,created_by=instance.created_by).order_by('-created_at').first()
           lm.updated_at = instance.updated_at
           lm.save()
       #print('INSTANCE ',instance.pk)
    except:
       pass

