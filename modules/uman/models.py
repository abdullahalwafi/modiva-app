from unittest.util import _MAX_LENGTH
from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import FileExtensionValidator
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from modules.core.validators import validate_content_type_pdf
#from modules.core.models import Pemda as RefPemda,  OverwriteStorage
#from modules.core.models import OverwriteStorage
from libs.models import BaseAuditModel


# Create your models here.
import uuid
import os


# added 3 Juni 2024

class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name


def get_file_surat_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('uman/surat_registrasi', filename)

class GroupAplikasi(models.Model):
    name = models.CharField('name', max_length=64, unique=True)
    abbr = models.CharField('abbr', max_length=15, unique=True)
    urutan = models.IntegerField(null=True, blank=True)
    aktif = models.BooleanField(null=False, blank=False, default=True)
    faw = models.CharField('faw', max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Group Aplikasi"


class Aplikasi(models.Model):
    name = models.CharField('name', max_length=100, unique=True)
    description = models.CharField(
        'description', max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='aplikasi',
                              max_length=100, null=True, blank=True)
    infografis = models.ImageField(
        upload_to='infografis', max_length=100, null=True, blank=True)
    faw = models.CharField('faw', max_length=20, null=True, blank=True)
    group = models.ForeignKey(
        GroupAplikasi, on_delete=models.CASCADE, null=True, blank=True)
    urutan = models.IntegerField(null=True, blank=True)
    aktif = models.BooleanField(null=False, blank=False, default=True)
    url = models.CharField('url', blank=True, null=True, max_length=255)
    as_modul = models.BooleanField(null=False, blank=False, default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Aplikasi"


class Menu(models.Model):
    aplikasi = models.ForeignKey(Aplikasi, on_delete=models.CASCADE)
    name = models.CharField('name', max_length=255)
    url = models.CharField('url', blank=True, null=True, max_length=255)
    urutan = models.IntegerField(null=True, blank=True)
    aktif = models.BooleanField(null=False, blank=False, default=True)
    faw = models.CharField(max_length=36, null=True, blank=True)
    description = models.CharField(
        'description', blank=True, null=True, max_length=255)
    isembed = models.BooleanField(default=False)
    url_embed = models.CharField(
        'url_embed', blank=True, null=True, max_length=255)
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='parent_menu_set',
    )
    # produk_id = models.IntegerField(null=True, blank=True)
    # Ditambahkan 31 Okt 2023 - menambah field as_beranda
    as_beranda = models.BooleanField(null=False, blank=False, default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Menu"




class EmbedMenu(models.Model):
    # enum_parameter = [('tahun', 'Tahun'), ('pemda', 'Pemda'), ('kode sakter', 'Kode Satker'),
    # ('kode pemda', 'Kode Pemda'),('provinsi', 'Provinsi'),('kementrian', 'Kementrian')]
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    secretkey = models.CharField('secretkey', max_length=255)
    url_metabase = models.CharField(
        'URL Metabase', blank=True, null=True, max_length=255)
    metabase_id = models.IntegerField(null=True, blank=True)
    # parameter = models.CharField(max_length=12, blank=True, null=True, choices=enum_parameter)
    param_tahun = models.BooleanField(null=True, blank=True, default=False)
    #param_pemda = models.BooleanField(null=True, blank=True, default=False)
    #param_kodsatker = models.BooleanField(null=True, blank=True, default=False)
    #param_kodpemda = models.BooleanField(null=True, blank=True, default=False)
    #param_provinsi = models.BooleanField(null=True, blank=True, default=False)
    #param_kementerian = models.BooleanField(
    #    null=True, blank=True, default=False)

    def __str__(self):
        return '%s ' % (self.menu.name)

    class Meta:
        verbose_name_plural = "Embed Menu"

# Added 28 at Oktober 2023


class Unit(models.Model):
    kd_unit = models.CharField(
        max_length=20, blank=False, null=False, unique=True)
    nm_unit = models.CharField(
        max_length=100, blank=False, null=False, unique=True)
    alamat = models.CharField(
        max_length=200, blank=True, null=True)
    kota = models.CharField(
        max_length=30, blank=True, null=True)
    is_active = models.BooleanField(null=False, blank=False, default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'uman_unit'
        verbose_name_plural = "Unit"

    def __str__(self):
        return self.nm_unit


class Jabatan(models.Model):
    kd_jabatan = models.CharField(
        max_length=20, blank=False, null=False, unique=True)
    nm_jabatan = models.CharField(max_length=100, blank=False, null=False)
    is_active = models.BooleanField(null=False, blank=False, default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'uman_jabatan'
        verbose_name_plural = "Jabatan"

    def __str__(self):
        return self.nm_jabatan


class Pegawai(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nip = models.CharField(max_length=40, blank=True, null=True, unique=True)
    nama = models.CharField(max_length=100, blank=True, null=True)
    no_hp = models.CharField(max_length=20, blank=True, null=True)
    no_wa = models.CharField(max_length=20, blank=True, null=True)
    kd_unit = models.ForeignKey(Unit, models.DO_NOTHING, blank=True, null=True)
    kd_jabatan = models.ForeignKey(
        Jabatan, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'uman_pegawai'
        verbose_name_plural = "Pegawai"

    def __str__(self):
        return self.user.username
# End of line - added at 28 Oktober 2023


class AdminUser(models.TextChoices):
      ADMIN = "admin","ADMIN"
      OPERATOR_PUSKESMAS = "operator puskesmas", "OPERATOR PUSKESMAS"
      OPERATOR_SEKOLAH = "operator sekolah", "OPERATOR SEKOLAH"


class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    #kode_satker = models.CharField(max_length=6, blank=True, null=True)
    no_hp = models.CharField(max_length=20, blank=True, null=True)
    no_wa = models.CharField(max_length=20, blank=True, null=True)
    kdunit = models.CharField(max_length=20, blank=True, null=True)
    foto_profil = models.ImageField(upload_to='uman/foto_profil', blank=True)
    nip = models.CharField(max_length=40, blank=True, null=True)
    nik = models.CharField(max_length=40, blank=True, null=True)
    #kd_kppn = models.CharField(max_length=3, blank=True, null=True)
    #kd_kanwil = models.CharField(max_length=3, blank=True, null=True)
    #kd_kementerian = models.CharField(max_length=20, blank=True, null=True)
    #opd = models.ForeignKey(Opd,on_delete=models.SET_NULL, blank=True, null=True)
    #uptd = models.ForeignKey(Uptd,on_delete=models.SET_NULL, blank=True, null=True)
    as_admin = models.CharField(max_length=20,choices=AdminUser.choices,blank=True, null=True)
    

    class Meta:
        managed = True
        db_table = 'uman_userdetail'
        verbose_name_plural = "User Detail"
        indexes = [
            #models.Index(fields=['name', 'affiliation_date'], name='name_afiliation_index'),  # Composite index
            #models.Index(fields=['kode_satker'], name='kode_satker_index'),  # Single-field index with a custom name
        ]

    def __str__(self):
        return self.user.username


class GroupMenu(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    menu = models.ManyToManyField(Menu)
    can_view = models.CharField(max_length=20,choices=AdminUser.choices,blank=True, null=True) 

    class Meta:
        managed = True
        db_table = 'uman_groupmenu'
        verbose_name_plural = "Group Menu"

    def __str__(self):
        return self.group.name


class AppConfig(BaseAuditModel):
    namespace = models.CharField(max_length=64)
    key = models.CharField(max_length=64)
    value = models.TextField()
    description = models.TextField(null=True, blank=True)

    class Meta:
        managed = True
        unique_together = (('namespace', 'key'),)
        verbose_name_plural = "Konfigurasi Aplikasi"

    def __str__(self):
        return f'{self.namespace} - {self.key}'
