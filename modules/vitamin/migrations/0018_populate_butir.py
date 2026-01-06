from django.db import migrations

def populate_butir(apps, schema_editor):
    distribusiobat = apps.get_model('vitamin', 'Distribusiobat')
    for stok in distribusiobat.objects.all():
        try:
            isi = int(stok.stokobat.masterobat.isi or 0)
            stok.butir = (stok.stok or 0) * isi
            stok.save()
        except:
            stok.butir = None
            stok.save()

class Migration(migrations.Migration):

    dependencies = [
        ('vitamin', '0017_distribusiobat_butir_distribusiobat_created_at_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_butir),
    ]
