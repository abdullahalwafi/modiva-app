
from django import forms
from .models import ContactMessage

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['puskesmas', 'email', 'phone', 'message']
        widgets = {
            'puskesmas': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Masukkan Nama Puskesmas', 'required': True}),
            'email': forms.EmailInput(attrs={
                'class': 'form-control rounded-3', 'placeholder': 'Masukkan Email', 'required': True,
                'oninvalid': "this.setCustomValidity('Format email tidak valid')",
                'oninput': "this.setCustomValidity('')",
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control rounded-3', 'placeholder': 'Masukkan Nomor Telepon', 'required': True,
                'pattern': '^[0-9]{10,15}$',
                'oninvalid': "this.setCustomValidity('Masukkan nomor telepon yang valid (10-15 digit angka)')",
                'oninput': "this.setCustomValidity('')",
            }),
            'message': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 4, 'placeholder': 'Silahkan isi pesan atau pertanyaan yang ingin di sampaikan', 'required': True}),
        }

    def __init__(self, *args, **kwargs):
        super(ContactMessageForm, self).__init__(*args, **kwargs)

        self.fields['puskesmas'].label = 'Kode Kecamatan Kota'
        self.fields['email'].label = 'Nama Kecamatan Kota'
        self.fields['phone'].label = 'Nama Alternatif'
        self.fields['message'].label = 'Garis Lintang'
