from django.db import migrations

def populate_butir(apps, schema_editor):
    Stokobat = apps.get_model('vitamin', 'Stokobat')
    for stok in Stokobat.objects.all():
        try:
            isi = int(stok.masterobat.isi or 0)
            stok.butir = (stok.stok or 0) * isi
            stok.save()
        except:
            stok.butir = None
            stok.save()

class Migration(migrations.Migration):

    dependencies = [
        ('vitamin', '0015_distribusiobat_created_at_distribusiobat_created_by_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_butir),
    ]
