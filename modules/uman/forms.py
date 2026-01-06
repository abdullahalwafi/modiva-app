from django import forms
from .models import (UserDetail, 
                     Menu, EmbedMenu, GroupMenu, GroupAplikasi,
                     Aplikasi, Unit, Jabatan,
                     Pegawai, AppConfig,
                     )
#from modules.core.models import Pemda
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group, Permission
from django.urls import resolve
from modules.core.core_libs import set_absolute_path


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Username',
                'class': 'form-control form-control-lg'
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '***********',
                'class': 'form-control form-control-lg'
            }
        )
    )


class UpdateFotoProfilForm(forms.ModelForm):
    class Meta:
        model = UserDetail
        fields = ['foto_profil']


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['kd_unit', 'nm_unit', 'alamat', 'kota', 'is_active']

    def __init__(self, *args, **kwargs):
        super(UnitForm, self).__init__(*args, **kwargs)
        self.fields['kd_unit'].label = 'Kode Unit'
        self.fields['nm_unit'].label = 'Nama Unit'
        self.fields['alamat'].label = 'Alamat'
        self.fields['kota'].label = 'Kota'
        self.fields['is_active'].label = 'Aktif'


class JabatanForm(forms.ModelForm):
    class Meta:
        model = Jabatan
        fields = ['kd_jabatan', 'nm_jabatan', 'is_active']

    def __init__(self, *args, **kwargs):
        super(JabatanForm, self).__init__(*args, **kwargs)
        self.fields['kd_jabatan'].label = 'Kode Jabatan'
        self.fields['nm_jabatan'].label = 'Nama Jabatan'


class PegawaiForm(forms.ModelForm):
    class Meta:
        model = Pegawai
        fields = ['user', 'nip', 'nama', 'no_wa',
                  'no_hp', 'kd_unit', 'kd_jabatan']

    def __init__(self, *args, **kwargs):
        super(PegawaiForm, self).__init__(*args, **kwargs)
        self.fields['kd_unit'].label = 'Kode Unit'
        self.fields['kd_jabatan'].label = 'Kode Jabatan'
        self.fields['nama'].label = 'Nama Lengkap'
        self.fields['user'].label = 'Username'
        self.fields['nip'].label = 'NIP'
        self.fields['no_wa'].label = 'Nomor WA'
        self.fields['no_hp'].label = 'Nomor HP'


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['aplikasi', 'name', 'url', 'urutan', 'aktif', 'faw',
                  'description', 'isembed', 'url_embed', 'parent', 'as_beranda']

    def __init__(self, *args, **kwargs):
        super(MenuForm, self).__init__(*args, **kwargs)
        qs = Aplikasi.objects.filter(
            aktif=True, as_modul=True).order_by('name')
        self.fields['aplikasi'].queryset = qs
        self.fields['as_beranda'].label = 'Sebagai Beranda'
        menus = Menu.objects.filter(aktif=True).order_by(
            'parent__urutan', 'parent__name')
        choices_menu = [('', '-------')]
        for menu in menus:
            if menu.parent is None or menu.parent == 0:
                # choices_menu.append( (f'{menu.id}',f'{menu.aplikasi} / {menu.name}') )
                choices_menu.append((f'{menu.id}', f'{menu.name}'))
                continue
            else:
                menu_label = [menu.name]
                m = menu
                for i in range(6):
                    try:
                        menu_label.insert(0, m.parent.name)
                        m = m.parent
                    except:
                        # menu_label.insert(0,menu.aplikasi.name)
                        choices_menu.append(
                            (f'{menu.id}', f'{" / ".join(menu_label)}'))
                        break
        self.fields['parent'].choices = choices_menu

    def clean_url(self):
        url = self.cleaned_data['url']
        try:
            if url.find('http') == 0:
                return url
        except:
            pass
        if url == None or url == '':
            return url
        if url:
            try:
                resolve(set_absolute_path(url.split('?')[0]))
            except:
                raise ValidationError(
                    "URL {} Not Valid or Not Found".format(url))
        return url


class EmbedMenuForm(forms.ModelForm):

    class Meta:
        model = EmbedMenu
        fields = ['menu', 'secretkey', 'url_metabase', 'metabase_id', 'param_tahun' ]
    # ---------ambil FK yg isembed saja--------------

    def __init__(self, *args, **kwargs):
        super(EmbedMenuForm, self).__init__(*args, **kwargs)
        # embedmenu yg sudah terpilih,tidak ditampilkan di select opt
        em = EmbedMenu.objects.all()
        # select opt yg isembed saja dan embedmenu yg sudah terpilih,tidak ditampilkan di select opt
        if self.instance.menu_id:
            em = EmbedMenu.objects.exclude(menu_id=self.instance.menu_id)
        qs = Menu.objects.filter(isembed=1).exclude(
            id__in=[x.menu_id for x in em]).order_by('name')

        self.fields['menu'].queryset = qs


class GroupMenuForm(forms.ModelForm):
    class Meta:
        model = GroupMenu
        fields = ['group', 'menu', 'can_view']

    def __init__(self, *args, **kwargs):
        super(GroupMenuForm, self).__init__(*args, **kwargs)
        menus = Menu.objects.filter(aktif=True).order_by(
            'aplikasi', 'urutan', 'name')
        choices_menu = []
        for menu in menus:
            if menu.parent is None or menu.parent == 0:
                choices_menu.append(
                    (f'{menu.id}', f'{menu.aplikasi} / {menu.name}'))
                continue
            else:
                menu_label = [menu.name]
                m = menu
                for i in range(6):
                    try:
                        menu_label.insert(0, m.parent.name)
                        m = m.parent
                    except:
                        menu_label.insert(0, menu.aplikasi.name)
                        choices_menu.append(
                            (f'{menu.id}', f'{" / ".join(menu_label)}'))
                        break
        self.fields['menu'].choices = choices_menu

    def clean_group(self):
        group = self.cleaned_data['group']
        obj = Group.objects.get(name=group)
        if GroupMenu.objects.filter(group=obj).count() > 0:
            if self.instance.pk:
                return group
            else:
                raise ValidationError(
                    "Groupmenu {} already Exist".format(group))
        else:
            return group


class GroupAplikasiForm(forms.ModelForm):
    class Meta:
        model = GroupAplikasi
        fields = ['name', 'abbr', 'urutan', 'aktif', 'faw']


class AplikasiForm(forms.ModelForm):
    class Meta:
        model = Aplikasi
        fields = ['name', 'description', 'image', 'infografis',
                  'faw', 'group', 'urutan', 'aktif', 'url', 'as_modul']


class UserDetailPasswordForm(forms.Form):
    password = forms.CharField(min_length=8, max_length=16, label='Password Baru',
                               widget=forms.PasswordInput(
                                   attrs={
                                       'placeholder': '***********',
                                       'class': 'form-control form-control-lg'
                                   }
                               )
                               )
    password2 = forms.CharField(min_length=8, max_length=16, label='Konfirmasi Password',
                                widget=forms.PasswordInput(
                                    attrs={
                                        'placeholder': '***********',
                                        'class': 'form-control form-control-lg'
                                    }
                                )
                                )


try:
    #from modules.tkd.models import RefKppn, RefKanwilpb
    tkd = True
except:
    tkd = False


class UserDetailCreateForm(forms.ModelForm):
    user = forms.CharField(max_length=75)
    email = forms.EmailField(max_length=100, required=False)
    #kode_satker = forms.ChoiceField(required=False)
    #kd_kementerian = forms.ChoiceField(required=False)
    #if tkd:
    #    kd_kppn = forms.ChoiceField(required=False)
    #    kd_kanwil = forms.ChoiceField(required=False)

    password = forms.CharField(min_length=8, max_length=16,
                               widget=forms.PasswordInput(
                                   attrs={
                                       'placeholder': '***********',
                                       'class': 'form-control form-control-lg'
                                   }
                               )
                               )
    group = forms.MultipleChoiceField(required=False)
    is_superuser = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False)

    class Meta:
        model = UserDetail
        fields = ['user', 'password', 'no_hp', 'no_wa',
                  'nip', 'nik', 'foto_profil','as_admin']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(UserDetailCreateForm, self).__init__(*args, **kwargs)
        self.fields['no_hp'].label = 'No HP'
        self.fields['no_wa'].label = 'No WA'
        self.fields['nip'].label = 'NIP'
        self.fields['nik'].label = 'NIK'
        self.fields['as_admin'].label = 'Sebagai Admin'
        self.fields['user'].label = 'Username'
        self.fields['is_superuser'].label = 'Sebagai Superuser'
        self.fields['is_active'].label = 'Aktif'
        #self.fields['kode_satker'].label = 'Kode Satker'
        self.fields['foto_profil'].label = 'Foto Profil'
        #self.fields['kd_kppn'].label = 'KPPN'
        #self.fields['kd_kanwil'].label = 'Kanwil'
        #self.fields['kd_kementerian'].label = 'Kode Kementerian'
        satker_choices = [('', '------'),]
        #satker_choices = satker_choices + [(p.kd_satker, f'{p.kd_satker} - {p.nm_pemda}')
        #                                   for p in Pemda.objects.filter(aktif=True).exclude(kd_satker=None).order_by('nm_pemda')]
        #self.fields['kode_satker'].choices = satker_choices
        kementerian_choices = [('', '------'),]
        #kementerian_choices = kementerian_choices + \
        #    [(kem.kode, kem.nama) for kem in Kementerian.objects.filter(
        #        aktif=True).order_by('urutan', 'nama')]
        #self.fields['kd_kementerian'].choices = kementerian_choices

        self.fields['group'].choices = [
            (g.id, f'{g.name}') for g in Group.objects.all().order_by('name')]

        if tkd:
            kppn_choices = [('', '------'),]
            kanwil_choices = [('', '------'),]
            

    def clean_user(self):
        u = self.cleaned_data['user']
        obj = User.objects.get(username=u)
        if UserDetail.objects.filter(user=obj).first():
            raise ValidationError("User {} already Exist".format(u))
        else:
            return obj

class UserDetailUpdateForm(forms.ModelForm):
    email = forms.EmailField(max_length=100, required=False)
    #kode_satker = forms.ChoiceField(required=False)
    #kd_kementerian = forms.ChoiceField(required=False)
    #if tkd:
        #kd_kppn = forms.ChoiceField(required=False)
        #kd_kanwil = forms.ChoiceField(required=False)
    group = forms.MultipleChoiceField(required=False)
    is_superuser = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False)

    class Meta:
        model = UserDetail
        fields = ['no_hp', 'no_wa', 'nip',
                  'nik', 'foto_profil','as_admin']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(UserDetailUpdateForm, self).__init__(*args, **kwargs)
        self.fields['no_hp'].label = 'No HP'
        self.fields['no_wa'].label = 'No WA'
        self.fields['nip'].label = 'NIP'
        self.fields['nik'].label = 'NIK'
        self.fields['as_admin'].label = 'Sebagai Admin'
        #self.fields['kode_satker'].label = 'Kode Satker'
        self.fields['foto_profil'].label = 'Foto Profil'
        #self.fields['kd_kppn'].label = 'KPPN'
        #self.fields['kd_kanwil'].label = 'Kanwil'
        self.fields['is_superuser'].label = 'Sebagai Superuser'
        self.fields['is_active'].label = 'Aktif'
        satker_choices = [('', '------'),]
        #satker_choices = satker_choices + [(p.kd_satker, f'{p.kd_satker} - {p.nm_pemda}')
        #                                   for p in Pemda.objects.filter(aktif=True).exclude(kd_satker=None).order_by('nm_pemda')]
        #self.fields['kode_satker'].choices = satker_choices
        self.fields['group'].choices = [
            (g.id, f'{g.name}') for g in Group.objects.all().order_by('name')]
        self.fields['group'].initial = [
            grp.id for grp in self.instance.user.groups.all()]
        self.fields['email'].initial = self.instance.user.email
        self.fields['is_superuser'].initial = self.instance.user.is_superuser
        self.fields['is_active'].initial = self.instance.user.is_active

class GroupCreateForm(forms.ModelForm):
    permission = forms.MultipleChoiceField(required=False)

    class Meta:
        model = Group
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(GroupCreateForm, self).__init__(*args, **kwargs)
        self.fields['permission'].choices = [
            (p.id, f'{p.name}') for p in Permission.objects.all().order_by('content_type', 'name')]


class GroupUpdateForm(forms.ModelForm):
    permission = forms.MultipleChoiceField(required=False)

    class Meta:
        model = Group
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(GroupUpdateForm, self).__init__(*args, **kwargs)
        self.fields['permission'].choices = [
            (p.id, f'{p.name}') for p in Permission.objects.all().order_by('content_type', 'name')]
        self.fields['permission'].initial = [
            gp.id for gp in self.instance.permissions.all().order_by('content_type', 'name')]


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(max_length=100, required=False)

    class Meta:
        model = UserDetail
        fields = ['no_hp', 'no_wa', 'nip', 'nik']

    def __init__(self, *args, **kwargs):
        super(UserProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['no_hp'].label = 'No HP'
        self.fields['no_wa'].label = 'No WA'
        self.fields['nip'].label = 'NIP'
        self.fields['nik'].label = 'NIK'
        self.fields['first_name'].label = 'Nama Depan'
        self.fields['last_name'].label = 'Nama Belakang'
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['email'].initial = self.instance.user.email


