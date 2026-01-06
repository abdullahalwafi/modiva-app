from django import forms
from .models import *
from modules.core.models import Pemda

class InfoPemdaForm(forms.ModelForm):
    class Meta:
        model = InfoPemda
        fields = ['groupmenu','keterangan','file_pdf','penerima']
    def __init__(self,*args, **kwargs):
        super(InfoPemdaForm, self).__init__(*args, **kwargs)
        self.fields['penerima'].choices = [(p.id,f'{p.nm_pemda.upper()}') for p in Pemda.objects.filter(aktif=True).exclude(nm_pemda=None).order_by('nm_pemda')]
        self.fields['groupmenu'].widget.attrs['placeholder'] = 'Group'
        self.fields['keterangan'].widget.attrs['placeholder'] = 'Keterangan'
        self.fields['file_pdf'].widget.attrs['placeholder'] = 'File PDF'
        self.fields['penerima'].widget.attrs['placeholder'] = 'Pemda penerima'
