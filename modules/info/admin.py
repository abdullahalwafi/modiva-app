from django.contrib import admin
from .models import *
# Register your models here.
class InfoPemdaAdmin(admin.ModelAdmin):
    list_display = ['keterangan','file_pdf']
    search_fields = ['keterangan','file_pdf']

admin.site.register(InfoPemda, InfoPemdaAdmin)

