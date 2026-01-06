from django.db import models
from django.core.validators import FileExtensionValidator

# Create your models here.

def custom_file_nama_gambar(instance, filename):
    # Extract information from the file instance (e.g., user, date, file type)
    #user = instance.user
        namapath = 'uploads/puskesmas/'
        namafile = instance.nama
        file_extension = filename.split('.')[-1]

    # Construct the new file name using the extracted information
        new_filename = f"{namapath}{namafile}.{file_extension}"

        return new_filename

def custom_file_nama_gambar_sekolah(instance, filename):
    # Extract information from the file instance (e.g., user, date, file type)
    #user = instance.user
        namapath = 'uploads/sekolah/'
        namafile = instance.nama
        file_extension = filename.split('.')[-1]

    # Construct the new file name using the extracted information
        new_filename = f"{namapath}{namafile}.{file_extension}"

        return new_filename

class Provinsi(models.Model):
    id = models.IntegerField(primary_key=True, blank=False, null=False)
    nama = models.CharField(max_length=150, blank=False, null=False)
    alt_nama = models.CharField(max_length=100, blank=False, null=False)
    latitude = models.FloatField(blank=True, null=True, default=0)
    longitude = models.FloatField(blank=True, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'provinsi'
        ordering = ["id"]
    
    def __str__(self):
        return self.nama

class KabKota(models.Model):
    id = models.IntegerField(primary_key=True, blank=False, null=False)
    provinsi = models.ForeignKey(Provinsi, on_delete=models.CASCADE, db_column='provinsi_id')
    nama = models.CharField(max_length=150, blank=False, null=False)
    alt_nama = models.CharField(max_length=100, blank=False, null=False)
    latitude = models.FloatField(blank=True, null=True, default=0)
    longitude = models.FloatField(blank=True, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'kabkota'
        ordering = ["id"]
    
    def __str__(self):
        return f"{self.provinsi.nama} - {self.nama}"

class Kecamatan(models.Model):
    id = models.IntegerField(primary_key=True, blank=False, null=False)
    kabkota = models.ForeignKey(KabKota, on_delete=models.CASCADE, db_column='kabkota_id')
    nama = models.CharField(max_length=150, blank=False, null=False)
    alt_nama = models.CharField(max_length=100, blank=False, null=False)
    latitude = models.FloatField(blank=True, null=True, default=0)
    longitude = models.FloatField(blank=True, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True 
        db_table = 'kecamatan'
        ordering = ["id"]

    def __str__(self):
        return f"{self.kabkota.nama} - {self.nama}"

class Kelurahan(models.Model):
    id = models.BigIntegerField(primary_key=True, blank=False, null=False)
    kecamatan = models.ForeignKey(Kecamatan,on_delete=models.CASCADE,db_column='kecamatan_id')
    nama = models.CharField(max_length=150, blank=False, null=False)
    alt_nama = models.CharField(max_length=100, blank=False, null=False)
    latitude = models.FloatField(blank=True, null=True, default=0)
    longitude = models.FloatField(blank=True, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'kelurahan'
        ordering = ["id"]

    def __str__(self):
        return f"{self.kecamatan.nama} - {self.nama}"

class Puskesmas(models.Model):
    kode = models.CharField(max_length=50, unique=True, blank=False, null=False)
    nama = models.CharField(max_length=150, blank=False, null=False)
    alamat = models.CharField(max_length=250, blank=True, null=True)
    telepon = models.CharField(max_length=50, blank=True, null=True)
    hp_informasi = models.CharField(max_length=20, blank=True, null=True)
    gps_koordinat = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    website = models.CharField(max_length=50, blank=True, null=True)
    kepala_puskesmas = models.CharField(max_length=100, blank=True, null=True)
    kelurahan = models.ForeignKey(Kelurahan,on_delete=models.CASCADE,db_column='kelurahan_id')
    gambar = models.ImageField(upload_to='uploads/puskesmas/', validators=[FileExtensionValidator(['jpg','jpeg','png','JPG','JPEG','PNG','svg','SVG'])],blank=True, null=True)
    deskripsi = models.TextField(blank=True, null=True)  # Tambahan field deskripsi
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    is_terdaftar = models.BooleanField(null=False, blank=False, default=False)
    

    class Meta:
        managed = True
        db_table = 'puskesmas'
        ordering = ["id"]

    def __str__(self):
        return self.nama
    
class Vitamin(models.Model):
    nama = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'vitamin'
        ordering = ["id"]

    def __str__(self):
        return self.nama

class JenjangPilihan(models.TextChoices):
    SD = 'SD', 'SD'
    SMP = 'SMP', 'SMP'
    SMA = 'SMA', 'SMA'
    
class Satuan(models.Model):
    nama = models.CharField(max_length=150, blank=True, null=True)
    keterangan = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'satuan'
        ordering = ["id"]

    def __str__(self):
        return self.nama
    

class Sekolah(models.Model):
    kode = models.CharField(max_length=50, unique=True, blank=False, null=False)
    nama = models.CharField(max_length=150, blank=False, null=False)
    alamat = models.CharField(max_length=250, blank=True, null=True)
    jenjang = models.CharField(
        max_length=10,
        choices=JenjangPilihan.choices,
        blank=False,
        null=False
    )
    telepon = models.CharField(max_length=50, blank=True, null=True)
    website = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    gps_koordinat = models.CharField(max_length=20, blank=True, null=True)
    kelurahan = models.ForeignKey(Kelurahan,on_delete=models.CASCADE,db_column='kelurahan_id')
    puskesmas = models.ForeignKey(Puskesmas,on_delete=models.CASCADE,db_column='puskesmas_id')
    gambar = models.ImageField(upload_to='uploads/sekolah/', validators=[FileExtensionValidator(['jpg','jpeg','png','JPG','JPEG','PNG','svg','SVG'])],blank=True, null=True)
    deskripsi = models.TextField(blank=True, null=True)  # Tambahan field deskripsi
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    
    # Tambahkan field status
    status = models.BooleanField(default=1)  # 1=aktif, 0=tidak aktif

    class Meta:
        managed = True
        db_table = 'sekolah'
        ordering = ["id"]

    def __str__(self):
        return self.nama
    

class MasterObat(models.Model):
    vitamin = models.ForeignKey(Vitamin,on_delete=models.CASCADE,db_column='vitamin_id')
    merk = models.CharField(max_length=100, blank=True, null=True, default='')
    pabrik = models.CharField(max_length=100, blank=True, null=True, default='')
    kadaluarsa = models.DateField(blank=True, null=True)
    isi = models.CharField(max_length=100, blank=True, null=True, default='')
    batchnumber = models.CharField(max_length=100, blank=True, null=True)
    satuan = models.ForeignKey(Satuan,on_delete=models.CASCADE,db_column='satuan_id')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'master_obat'
        ordering = ["id"]

    def __str__(self):
        return f'{self.merk} - {self.batchnumber}'


class Stokobat(models.Model):
    tgl_terima = models.DateField(blank=True, null=True)
    terima = models.IntegerField(blank=True, null=True)
    stok = models.IntegerField(blank=True, null=True)  # jumlah satuan besar
    puskesmas = models.ForeignKey(Puskesmas,on_delete=models.CASCADE,db_column='puskesmas_id')
    keterangan = models.CharField(max_length=250, blank=True, null=True)
    masterobat = models.ForeignKey(MasterObat,on_delete=models.CASCADE,db_column='masterobat_id')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    butir = models.IntegerField(blank=True, null=True)  # total butir
    
    class Meta:
        managed = True
        db_table = 'stok_obat'
        ordering = ["id"]

    def __str__(self):
        if self.tgl_terima:
            formatted_date = self.tgl_terima.strftime('%d-%m-%Y')
        else:
            formatted_date = 'Tanggal tidak tersedia'
        return f'{formatted_date} - {self.masterobat.merk} - {self.stok} - {self.butir} - {self.puskesmas.nama}'

    def save(self, *args, **kwargs):
        try:
            self.butir = (self.stok or 0) * int(self.masterobat.isi)
        except (ValueError, TypeError):
            self.butir = None
        super().save(*args, **kwargs)


class Distribusiobat(models.Model):
    tgl_kirim = models.DateField(blank=True, null=True)
    tgl_terima = models.DateField(blank=True, null=True)
    jumlah_terima = models.IntegerField(blank=True, null=True)
    stok = models.IntegerField(blank=True, null=True)
    butir = models.IntegerField(blank=True, null=True)  # total butir
    sekolah = models.ForeignKey(Sekolah,on_delete=models.CASCADE,db_column='sekolah_id')
    stokobat = models.ForeignKey(Stokobat,on_delete=models.CASCADE,db_column='stokobat_id')
    puskesmas = models.ForeignKey(Puskesmas,on_delete=models.CASCADE,db_column='puskesmas_id')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'distribusi_obat'
        ordering = ["id"]

    def __str__(self):
        return f'{self.stokobat.masterobat.vitamin.nama} - Tanggal Terima : {self.tgl_terima} - Sekolah : {self.sekolah.nama}'
    
class Siswa(models.Model):
    GENDER_CHOICES = (
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    )
    nis = models.CharField(max_length=10, unique=True)
    nama = models.CharField(max_length=45)
    tmp_lahir = models.CharField(max_length=45, blank=True)
    tgl_lahir = models.DateField(null=True, blank=True)
    email = models.EmailField(max_length=50, blank=True)
    sekolah = models.ForeignKey(Sekolah,on_delete=models.PROTECT,related_name='siswa')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'siswa'
        indexes = [
            models.Index(fields=['nis']),
            models.Index(fields=['sekolah']),
        ]
        ordering = ["id"]

    def __str__(self):
        return f'{self.nis} - {self.nama}'


class SiswaHB(models.Model):
    siswa = models.ForeignKey(Siswa,on_delete=models.CASCADE,related_name='rekam_hb'
    )
    tahun = models.PositiveSmallIntegerField()
    # Hemoglobin (g/dL) – gunakan Decimal agar presisi
    hb = models.DecimalField(max_digits=4, decimal_places=1)  # contoh: 12.5
    keterangan = models.CharField(max_length=45, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'siswa_hb'
        verbose_name = 'Rekam HB Siswa'
        verbose_name_plural = 'Rekam HB Siswa'
        indexes = [
            models.Index(fields=['siswa', 'tahun']),
        ]
        #unique_together = [('siswa', 'tahun')]  # satu entry per tahun per siswa

    def __str__(self):
        return f'HB {self.siswa.nis} ({self.tahun}) = {self.hb} g/dL'

class Distribusisiswa(models.Model):
    nis = models.CharField(max_length=10, blank=True, null=True)
    nama_siswa = models.CharField(max_length=100, blank=True, null=True)
    jumlah = models.IntegerField(blank=True, null=True)
    tgl_terima = models.DateField(blank=True, null=True)
    kelas = models.CharField(max_length=10, blank=True, null=True)
    sekolah = models.ForeignKey(Sekolah,on_delete=models.CASCADE,db_column='sekolah_id')
    vitamin = models.ForeignKey(Vitamin,on_delete=models.CASCADE,db_column='vitamin_id')
    siswa = models.ForeignKey(Siswa,on_delete=models.CASCADE,db_column='siswa_id')
    distribusiobat = models.ForeignKey(Distribusiobat,on_delete=models.CASCADE,db_column='distobat_id')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'distribusi_siswa'
        ordering = ["id"]

    def __str__(self):
        return f'{self.nis} - {self.nama_siswa}'
