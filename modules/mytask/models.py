from django.db import models
from modules.uman.models import Menu
from django.contrib.auth.models import User
# Create your models here.
    
class Produk(models.Model):
    produk_id = models.CharField(max_length=64,unique=True,null=False,blank=False)
    nama = models.CharField(max_length=128,null=False,blank=False)
    norma_waktu = models.IntegerField(blank=True, null=True)
    aktif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)


    class Meta:
         managed = True
         db_table = 'mytask"."produk'
         verbose_name_plural = "Produk"

    def __str__(self):
         return f"{self.produk_id}"

class MenuProduk(models.Model):
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    menu = models.ManyToManyField(Menu)
    aktif = models.BooleanField(default=True)
    class Meta:
         managed = True
         db_table = 'mytask"."menu_produk'
         verbose_name_plural = "Menu Produk"

    def __str__(self):
         return f"{self.id} - {self.produk.nama}"


class HasilKirim(models.Model):
    produk = models.ForeignKey(Produk, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING,blank=True, null=True)
    tanggal = models.DateField()
    waktu_awal = models.TimeField()
    waktu_akhir = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)


    class Meta:
         managed = True
         db_table = 'mytask"."hasil_kirim'
         verbose_name_plural = "History Hasil Kirim"

    def __str__(self):
         return self.produk.produk_id


class LogMenu(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE,blank=True,null=True)
    data = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)


    class Meta:
         managed = True
         db_table = 'mytask"."log_menu'
         verbose_name_plural = "Log Aktifitas Menu"

    def __str__(self):
         return f"{self.id} - {self.menu.name}"

    @property
    def user(self):
        return User.objects.filter(id=self.created_by).prefetch_related('userdetail').first() 
