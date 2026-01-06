import datetime
from .models import *
from django import forms
from modules.vitamin.models import *
from modules.landingpage.models import ContactMessage
from datetime import date
from django.db import transaction
from django.core.exceptions import ValidationError


class ProvinsiForm(forms.ModelForm):
    class Meta:
        model = Provinsi
        fields = ['id','nama','alt_nama','latitude','longitude']
        labels = {
            'id': 'Kode Provinsi',
            'nama': 'Nama Provinsi',
            'alt_nama': 'Nama Alternatif',
            'latitude': 'Garis Lintang',
            'longitude': 'Garis Bujur',
        }

class KabKotaForm(forms.ModelForm):

    class Meta:
        model = KabKota
        fields = ['id','nama','alt_nama','latitude','longitude', 'provinsi']

    def __init__(self, *args, **kwargs):
        super(KabKotaForm, self).__init__(*args, **kwargs)

        self.fields['id'].label = 'Kode Kabupaten Kota'
        self.fields['nama'].label = 'Nama Kabupaten Kota'
        self.fields['alt_nama'].label = 'Nama Alternatif'
        self.fields['latitude'].label = 'Garis Lintang'
        self.fields['longitude'].label = 'Garis Bujur'
        self.fields['provinsi'].label = 'Provinsi'

   

class KecamatanForm(forms.ModelForm):

    class Meta:
        model = Kecamatan
        fields = ['id','nama','alt_nama','latitude','longitude', 'kabkota']

    def __init__(self, *args, **kwargs):
        super(KecamatanForm, self).__init__(*args, **kwargs)

        self.fields['id'].label = 'Kode Kecamatan Kota'
        self.fields['nama'].label = 'Nama Kecamatan Kota'
        self.fields['alt_nama'].label = 'Nama Alternatif'
        self.fields['latitude'].label = 'Garis Lintang'
        self.fields['longitude'].label = 'Garis Bujur'
        self.fields['kabkota'].label = 'Kabupaten Kota'


class KelurahanForm(forms.ModelForm):
    class Meta:
        model = Kecamatan
        fields = ['id','nama','alt_nama','latitude','longitude']



class PuskesmasForm(forms.ModelForm):

    class Meta:
        model = Puskesmas
        fields = ['kode','nama','alamat','telepon','hp_informasi', 'gps_koordinat', 'email', 'website', 'kepala_puskesmas', 'kelurahan', 'deskripsi', 'gambar', 'is_terdaftar']
    
    def __init__(self, *args, **kwargs):
        super(PuskesmasForm, self).__init__(*args, **kwargs)

        self.fields['kode'].label = 'Kode Puskesmas'
        self.fields['nama'].label = 'Nama Puskesmas'
        self.fields['alamat'].label = 'Alamat'
        self.fields['telepon'].label = 'Telepon'
        self.fields['hp_informasi'].label = 'No Hp'
        self.fields['gps_koordinat'].label = 'GPS Koordinat'
        self.fields['email'].label = 'Email'
        self.fields['website'].label = 'Website'
        self.fields['kepala_puskesmas'].label = 'Kepala Puskesmas'
        self.fields['kelurahan'].label = 'Kelurahan'
        self.fields['deskripsi'].label = 'Deskripsi'
        self.fields['gambar'].label = 'Gambar'
        self.fields['is_terdaftar'].label = 'Aktif Terdaftar'

class PuskesmasForm2(forms.ModelForm):

    class Meta:
        model = Puskesmas
        fields = ['kode','nama','is_terdaftar']
    
    def __init__(self, *args, **kwargs):
        super(PuskesmasForm2, self).__init__(*args, **kwargs)

        self.fields['kode'].label = 'Kode Puskesmas'
        self.fields['nama'].label = 'Nama Puskesmas'
        self.fields['is_terdaftar'].label = 'Terdaftar'

        # 🔒 Disable fields
        self.fields['kode'].disabled = True
        self.fields['nama'].disabled = True



class VitaminForm(forms.ModelForm):
    class Meta:
        model = Vitamin
        fields = ['nama']
    
    def __init__(self, *args, **kwargs):
        super(VitaminForm, self).__init__(*args, **kwargs)

        self.fields['nama'].label = 'Nama'
        self.fields['nama'].required = True


class SatuanForm(forms.ModelForm):
    class Meta:
        model = Satuan
        fields = ['nama','keterangan']
    
    def __init__(self, *args, **kwargs):
        super(SatuanForm, self).__init__(*args, **kwargs)

        self.fields['nama'].label = 'Nama'
        self.fields['keterangan'].label = 'Keterangan'
        self.fields['nama'].required = True


class SekolahForm(forms.ModelForm):
    STATUS_CHOICES = (
        (1, 'Aktif'),
        (0, 'Tidak Aktif'),
    )

    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select)

    class Meta:
        model = Sekolah
        fields = [
            'kode','nama','alamat','jenjang','telepon','website','email',
            'kelurahan','puskesmas','deskripsi','gps_koordinat','gambar','status'
        ]
    
    def __init__(self, *args, **kwargs):
        super(SekolahForm, self).__init__(*args, **kwargs)

        self.fields['kode'].label = 'Kode Sekolah'
        self.fields['nama'].label = 'Nama Sekolah'
        self.fields['alamat'].label = 'Alamat'
        self.fields['telepon'].label = 'Telepon'
        self.fields['jenjang'].label = 'Jenjang'
        self.fields['website'].label = 'Website'
        self.fields['email'].label = 'Email'
        self.fields['kelurahan'].label = 'Kelurahan'
        self.fields['puskesmas'].label = 'Puskesmas'
        self.fields['deskripsi'].label = 'Deskripsi'
        self.fields['gps_koordinat'].label = 'GPS Koordinat'
        self.fields['gambar'].label = 'Gambar'
        self.fields['status'].label = 'Status'


class MasterObatForm(forms.ModelForm):

    kadaluarsa = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )

    class Meta:
        model = MasterObat
        fields = ['vitamin','satuan','merk','pabrik','kadaluarsa','isi','batchnumber']
    
    def __init__(self, *args, **kwargs):
        super(MasterObatForm, self).__init__(*args, **kwargs)
        
        self.fields['vitamin'].label = 'Vitamin'
        self.fields['satuan'].label = 'Satuan'
        self.fields['merk'].label = 'Merk'
        self.fields['pabrik'].label = 'Pabrik'
        self.fields['kadaluarsa'].label = 'Tanggal Kadaluarsa'
        self.fields['isi'].label = 'Isi'
        self.fields['batchnumber'].label = 'Batch Number'

     
class StokObatForm(forms.ModelForm):
    tgl_terima = forms.DateField(
        required=True,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d'
        ),
    )

    class Meta:
        model = Stokobat
        fields = ['masterobat', 'tgl_terima', 'terima', 'stok', 'butir', 'keterangan']

    def __init__(self, *args, **kwargs):
        super(StokObatForm, self).__init__(*args, **kwargs)

        self.fields['masterobat'].queryset = MasterObat.objects.select_related('vitamin').all()
        self.fields['masterobat'].label_from_instance = (
            lambda obj: f"{obj.vitamin.nama} - {obj.merk} ({obj.satuan})"
        )

        self.fields['masterobat'].label = 'Master Obat'
        self.fields['tgl_terima'].label = 'Tanggal Terima'
        self.fields['terima'].label = 'Jumlah Diterima Puskesmas'
        self.fields['stok'].label = 'Stok'
        self.fields['butir'].label = 'Butir'
        self.fields['keterangan'].label = 'Keterangan'

        # isi otomatis tanggal hari ini
        if not self.instance.pk:
            self.fields['tgl_terima'].initial = date.today().strftime('%Y-%m-%d')

        # field readonly
        self.fields['stok'].widget.attrs['readonly'] = True
        self.fields['butir'].widget.attrs['readonly'] = True

        # field yang dikunci saat edit
        if self.instance and self.instance.pk:
            self.fields['masterobat'].disabled = True
            self.fields['terima'].disabled = True
            self.fields['stok'].disabled = True
            self.fields['butir'].disabled = True
class DisObatForm(forms.ModelForm):
    tgl_kirim = forms.DateField(
        required=True,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d'
        ),
    )
    tgl_terima = forms.DateField(
        required=True,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d'
        ),
    )

    class Meta:
        model = Distribusiobat
        fields = ['sekolah', 'stokobat', 'jumlah_terima', 'stok', 'butir', 'tgl_kirim', 'tgl_terima']
        widgets = {
            'stok': forms.HiddenInput(),
            'butir': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Label kolom
        self.fields['sekolah'].label = 'Sekolah'
        self.fields['stokobat'].label = 'Stok Obat'
        self.fields['jumlah_terima'].label = 'Jumlah Diterima Sekolah'
        self.fields['tgl_kirim'].label = 'Tanggal Kirim'
        self.fields['tgl_terima'].label = 'Tanggal Terima'

        # Default tanggal
        if not self.instance.pk:
            today = date.today()
            self.fields['tgl_kirim'].initial = today.strftime('%Y-%m-%d')
            self.fields['tgl_terima'].initial = today.strftime('%Y-%m-%d')

        # Queryset stokobat sesuai puskesmas user
        try:
            puskesmas = Puskesmas.objects.get(kode=user)
            self.fields['stokobat'].queryset = (
                Stokobat.objects.filter(puskesmas=puskesmas)
                .select_related("masterobat__vitamin")
            )
            self.fields['stokobat'].label_from_instance = (
                lambda obj: f"Stok: {obj.stok} - {obj.masterobat.vitamin.nama} - "
                            f"{obj.masterobat.merk} ({obj.masterobat.satuan}) "
                            f"- Exp: {obj.masterobat.kadaluarsa.strftime('%d-%m-%Y') if obj.masterobat.kadaluarsa else '-'}"
            )
        except Puskesmas.DoesNotExist:
            self.fields['stokobat'].queryset = Stokobat.objects.none()

        # Kalau edit → disable field tertentu
        if self.instance and self.instance.pk:
            self.fields['stokobat'].disabled = True
            self.fields['jumlah_terima'].disabled = True
            self.fields['butir'].disabled = True

    def clean_jumlah_terima(self):
        jumlah = self.cleaned_data.get('jumlah_terima')
        if not jumlah or jumlah <= 0:
            raise ValidationError("Jumlah harus lebih dari 0.")
        return jumlah

    def clean(self):
        cleaned_data = super().clean()
        stokobat = cleaned_data.get('stokobat')
        jumlah = cleaned_data.get('jumlah_terima')

        if stokobat and jumlah and not self.instance.pk:
            # Validasi stok cukup
            if stokobat.stok < jumlah:
                raise ValidationError({
                    "jumlah_terima": f"Stok tidak cukup (tersedia {stokobat.stok})."
                })

        # Hapus field hidden biar gak ganggu saat save()
        cleaned_data.pop('stok', None)
        cleaned_data.pop('butir', None)

        return cleaned_data

    def save(self, commit=True):
        """
        Simpan data distribusi tanpa mengubah stok.
        Pengurangan stok dilakukan di view (form_valid) agar tidak dobel.
        """
        instance = super().save(commit=False)
        stokobat = self.cleaned_data.get('stokobat')
        jumlah_baru = self.cleaned_data.get('jumlah_terima')

        if stokobat and jumlah_baru:
            isi = int(getattr(stokobat.masterobat, 'isi', 1)) or 1
            instance.stok = jumlah_baru
            instance.butir = int(jumlah_baru) * isi

        if commit:
            instance.save()
        return instance

class DistSiswaForm(forms.ModelForm):


    tgl_terima = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )

    class Meta:
        model = Distribusisiswa
        fields = ['siswa','kelas', 'tgl_terima','jumlah','vitamin','distribusiobat']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # get user from kwargs
        super(DistSiswaForm, self).__init__(*args, **kwargs)

        #self.fields['nis'].label = 'NIS'
        #self.fields['nama_siswa'].label = 'Nama Siswa'
        self.fields['siswa'].label = 'Siswa'
        self.fields['jumlah'].label = 'Jumlah'
        self.fields['tgl_terima'].label = 'Tanggal Terima'
        self.fields['kelas'].label = 'Kelas'
        self.fields['vitamin'].label = 'Vitamin'
        self.fields['distribusiobat'].label = 'Stok Obat'
     

        self.fields['tgl_terima'].initial = date.today

        self.fields['jumlah'].required = True

        try:
            sekolah = Sekolah.objects.get(kode=user)
            sekolah_id = sekolah.id
            self.fields['siswa'].queryset = Siswa.objects.filter(sekolah__id=sekolah_id)
        except Sekolah.DoesNotExist:
            print("Sekolah dengan kode tersebut tidak ditemukan.")
            self.fields['siswa'].queryset = Siswa.objects.none()

        try:
            sekolah = Sekolah.objects.get(kode=user)
            sekolah_id = sekolah.id
            self.fields['distribusiobat'].queryset = Distribusiobat.objects.filter(sekolah__id=sekolah_id)
        except Sekolah.DoesNotExist:
            print("Sekolah dengan kode tersebut tidak ditemukan.")
            self.fields['distribusiobat'].queryset = Distribusiobat.objects.none()
    
    def clean_jumlah_terima(self):
        jumlah = self.cleaned_data.get('jumlah')
        if jumlah is None or jumlah <= 0:
            raise ValidationError("Jumlah harus lebih dari 0.")
        return jumlah

    def clean(self):
        cleaned_data = super().clean()
        distribusiobat = cleaned_data.get('distribusiobat')
        jumlah = cleaned_data.get('jumlah')

        # Only validate stok if both fields are present
        if distribusiobat and jumlah:
            with transaction.atomic():
                so = Distribusiobat.objects.select_for_update().get(pk=distribusiobat.pk)
                if so.stok < jumlah:
                    raise ValidationError(
                        {"jumlah": f"Stok tidak cukup (tersedia {so.stok})."}
                    )
        return cleaned_data 


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['puskesmas','email','message','is_read']

    def __init__(self, *args, **kwargs):
        super(ContactMessageForm, self).__init__(*args, **kwargs)

        self.fields['puskesmas'].label = 'Puskesmas'
        self.fields['email'].label = 'Email'
        self.fields['message'].label = 'Pesan'
        self.fields['is_read'].label = 'Status Baca'

        self.fields['puskesmas'].disabled = True  # disables editing
        self.fields['email'].disabled = True  # disables editing
        self.fields['message'].disabled = True  # disables editing


class SiswaForm(forms.ModelForm):
    class Meta:
        model = Siswa
        fields = ['nis', 'nama', 'tmp_lahir', 'tgl_lahir', 'email', 'gender']
        widgets = {
            'tgl_lahir': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nis': forms.TextInput(attrs={'class': 'form-control'}),
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'tmp_lahir': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nis': 'Nomor Induk Siswa',
            'nama': 'Nama Lengkap',
            'tmp_lahir': 'Tempat Lahir',
            'tgl_lahir': 'Tanggal Lahir',
            'email': 'Alamat Email',
            'gender': 'Jenis Kelamin',
        }

class SiswaHbForm(forms.ModelForm):
    class Meta:
        model = SiswaHB
        fields = ['siswa', 'tahun', 'hb', 'keterangan']
       
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # get user from kwargs
        super(SiswaHbForm, self).__init__(*args, **kwargs)
        self.fields['siswa'].label = 'Siswa'
        self.fields['tahun'].label = 'Tahun'
        self.fields['hb'].label = 'Hb'
        self.fields['keterangan'].label = 'Keterangan'

        try:
            sekolah = Sekolah.objects.get(kode=user)
            sekolah_id = sekolah.id
            self.fields['siswa'].queryset = Siswa.objects.filter(sekolah__id=sekolah_id)
        except Sekolah.DoesNotExist:
            print("Sekolah dengan kode tersebut tidak ditemukan.")
            self.fields['siswa'].queryset = Siswa.objects.none()

    def clean_tahun(self):
        tahun = self.cleaned_data['tahun']
        from datetime import date
        if tahun < 2000 or tahun > date.today().year + 1:
            raise forms.ValidationError("Tahun tidak valid.")
        return tahun

    def clean_hb(self):
        hb = self.cleaned_data['hb']
        if hb is not None and (hb < 0 or hb > 25):
            raise forms.ValidationError("Nilai Hb di luar rentang wajar.")
        return hb