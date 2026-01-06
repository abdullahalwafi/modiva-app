from django.db import models

class BaseAuditModel(models.Model):
    id = models.AutoField(primary_key=True,unique=True,editable=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    class Meta:
        abstract = True
