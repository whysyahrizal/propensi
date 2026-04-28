# Generated manually for schedules → notifikasi integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifikasi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notifikasi',
            name='tipe',
            field=models.CharField(
                choices=[
                    ('info', 'Info'),
                    ('cuti', 'Cuti'),
                    ('sprin', 'Sprin'),
                    ('presensi', 'Presensi'),
                    ('jadwal', 'Jadwal Piket'),
                    ('sistem', 'Sistem'),
                ],
                default='info',
                max_length=20,
                verbose_name='Tipe',
            ),
        ),
    ]
