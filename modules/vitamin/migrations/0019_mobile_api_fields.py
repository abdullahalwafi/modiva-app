from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('vitamin', '0018_populate_butir'),
    ]

    operations = [
        migrations.AddField(
            model_name='siswa',
            name='berat_badan',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='siswa',
            name='tinggi_badan',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='distribusisiswa',
            name='bukti_foto',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/bukti_konsumsi/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG'])]),
        ),
        migrations.AddField(
            model_name='distribusisiswa',
            name='keterangan',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='distribusisiswa',
            name='status_konsumsi',
            field=models.CharField(blank=True, default='belum', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='distribusisiswa',
            name='tanggal_konsumsi',
            field=models.DateField(blank=True, null=True),
        ),
    ]
