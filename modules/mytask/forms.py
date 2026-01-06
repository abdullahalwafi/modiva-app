from django import forms
from .models import *
from datetime import datetime
from modules.uman.models import Menu
from django.core.exceptions import ValidationError

class ProdukForm(forms.ModelForm):
    class Meta:
        model = Produk
        fields = ['produk_id','nama','aktif']
    def __init__(self, *args, **kwargs):
        super(ProdukForm, self).__init__(*args, **kwargs)
        self.fields['produk_id'].label = 'Tahapan ID'

class MenuProdukForm(forms.ModelForm):
    class Meta:
        model = MenuProduk
        fields = ['produk','aktif','menu']
    def __init__(self, *args, **kwargs):
        super(MenuProdukForm, self).__init__(*args, **kwargs)
        try:
             mp = MenuProduk.objects.exclude(produk=self.instance.produk).values_list('menu',flat=True)
        except:
             mp = MenuProduk.objects.all().values_list('menu',flat=True)
        #self.fields['menu'].choices = [ (x.id,x.name) for x in Menu.objects.exclude(id__in=mp).order_by('name') ]

        menus = Menu.objects.filter(aktif=True).order_by('aplikasi','urutan','name')
        choices_menu = []
        for menu in menus:
               if menu.parent is None or menu.parent == 0:
                    choices_menu.append( (f'{menu.id}',f'{menu.aplikasi} / {menu.name}') )
                    continue
               else:
                    try:
                        level1 = menu.parent.parent.parent.name
                    except:
                        try:
                            level1 = menu.parent.parent.name
                        except:
                            level1 = menu.parent.name
                    try:
                        level2 = menu.parent.parent.name
                        if level2 == level1:
                             level2 = menu.parent.name
                    except:
                        level2 = menu.parent.name
                        if level2 == level1:
                             level2 = None
                    if level2 and level1:
                        choices_menu.append( (f'{menu.id}',f'{menu.aplikasi} / {level1} / {level2} / {menu.name}') )
                    else:
                        choices_menu.append( (f'{menu.id}',f'{menu.aplikasi} / {level1} / {menu.name}') )
        self.fields['menu'].choices = choices_menu

class KirimForm(forms.Form):
      produk_id = forms.IntegerField(widget=forms.HiddenInput(),required=True)
      #menu_id = forms.IntegerField(widget=forms.HiddenInput())
      tanggal = forms.DateField(required=True)
      waktu_awal = forms.TimeField(required=True)
      waktu_akhir = forms.TimeField(required=True)
      def clean_waktu_akhir(self):
          waktu_awal = self.cleaned_data.get("waktu_awal")
          waktu_akhir = self.cleaned_data.get("waktu_akhir")
          if  waktu_akhir > waktu_awal:
              return waktu_akhir
          else:
              raise ValidationError("Waktu akhir harus lebih besar dari waktu awal")

