from django.contrib import admin
from .models import (Pegawai, Unit, Aplikasi, Menu,Jabatan,
                     GroupAplikasi, EmbedMenu, UserDetail, GroupMenu,
                     AppConfig
                     )
from django.utils.html import mark_safe
from django.urls import reverse
from django.utils.http import urlencode


admin.site.site_header = 'CORESIKD ADMINISTRATION'
admin.site.index_title = 'Coresikd site administration'
admin.site.site_title = 'CORESIKD Adminsitration'
# Register your models here.


class GroupAplikasiAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbr', 'urutan', 'aktif']
    search_fields = ['name', 'abbr']


admin.site.register(GroupAplikasi, GroupAplikasiAdmin)


class AplikasiAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'url', 'urutan', 'as_modul', 'aktif']
    list_filter = ['group', 'as_modul']
    search_fields = ['name', 'group__name', 'url']


admin.site.register(Aplikasi, AplikasiAdmin)


class MenuAdmin(admin.ModelAdmin):
    list_display = ['name', 'aplikasi', 'url',
                    'parent', 'isembed', 'url_embed']
    search_fields = ['aplikasi__name', 'name', 'url', 'parent__name']


admin.site.register(Menu, MenuAdmin)


class EmbedMenuAdmin(admin.ModelAdmin):
    list_display = ['menu', 'secretkey', 'url_metabase', 'metabase_id', 'param_tahun',]


admin.site.register(EmbedMenu, EmbedMenuAdmin)


class UnitAdmin(admin.ModelAdmin):
    list_display = ['kd_unit', 'nm_unit', 'is_active']
    search_fields = ['kd_unit', 'nm_unit', 'is_active']
    ordering = ('kd_unit',)


admin.site.register(Unit, UnitAdmin)

#class JabatanAdmin(admin.ModelAdmin):
#    list_display = ['kd_jabatan', 'nm_jabatan', 'is_active']
#    search_fields = ['kd_jabatan', 'nm_jabatan', 'is_active']
#    ordering = ('kd_jabatan',)


admin.site.register(Jabatan)


class PegawaiAdmin(admin.ModelAdmin):
    list_display = ['user', 'nip', 'no_hp', 'no_wa', 'kd_unit', 'kd_jabatan']
    search_fields = ['user', 'nip', 'no_hp', 'no_wa', 'kd_unit', 'kd_jabatan']
    ordering = ('user',)


admin.site.register(Pegawai, PegawaiAdmin)


class UserDetailAdmin(admin.ModelAdmin):
    list_display = ['user', 'no_hp', 'no_wa']
    search_fields = ['user__username', 'no_hp', 'no_wa']
    ordering = ('user',)


admin.site.register(UserDetail, UserDetailAdmin)


class GroupMenuAdmin(admin.ModelAdmin):
    list_display = ('group', 'list_menu')

    ordering = ('group',)

    def list_menu(self, obj):
        url = reverse("admin:uman_menu_change", args=(obj.id,))
        return mark_safe("<ul>"+"\n".join(['<li><A href="%s">%s</A></li>' % (url, m.name) for m in obj.menu.all()])+"</ul>")


admin.site.register(GroupMenu, GroupMenuAdmin)
admin.site.register(AppConfig)
