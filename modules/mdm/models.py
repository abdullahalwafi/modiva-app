from django.db import models


class MdmManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().using("mdm")

class MasterModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    objects = MdmManager()
    def __str__(self):
        return self.name

class TableSetting(models.Model):
    id =  models.TextField(primary_key=True)
    nama =  models.TextField(blank=True, null=True)
    list_data =  models.TextField(blank=True, null=True)
    status =  models.TextField(blank=True, null=True)
    uraian_table =  models.TextField(blank=True, null=True)

    objects = MdmManager()
    
    class Meta:
        managed = True
        db_table = 'table_setting'
        ordering = ('id',)

class ExcelData(models.Model):
    file = models.FileField(upload_to='uploads/')