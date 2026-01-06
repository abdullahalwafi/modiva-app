from django.contrib import admin


# Register your models here.
from .models import * 

admin.site.site_header = 'CORESIKD ADMINISTRATION'
admin.site.index_title = 'Coresikd site administration'
admin.site.site_title = 'CORESIKD Adminsitration'

class LogMenuAdmin(admin.ModelAdmin):
    list_display = ['menu','created_by','created_at']
    list_filter = ['menu','created_at','created_by']
    search_fields = ['menu','created_by','data','created_at']

admin.site.register(LogMenu, LogMenuAdmin)
admin.site.register(Produk)
admin.site.register(HasilKirim)
