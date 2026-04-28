from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0005_role_display_label'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notifikasi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('judul', models.CharField(max_length=255, verbose_name='Judul')),
                ('pesan', models.TextField(verbose_name='Pesan')),
                ('tipe', models.CharField(
                    choices=[
                        ('info', 'Info'),
                        ('cuti', 'Cuti'),
                        ('sprin', 'Sprin'),
                        ('presensi', 'Presensi'),
                        ('sistem', 'Sistem'),
                    ],
                    default='info', max_length=20, verbose_name='Tipe'
                )),
                ('is_read', models.BooleanField(default=False, verbose_name='Sudah Dibaca')),
                ('link', models.CharField(blank=True, max_length=500, verbose_name='Link Terkait')),
                ('dibuat_pada', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Dibuat Pada')),
                ('dibaca_pada', models.DateTimeField(blank=True, null=True, verbose_name='Dibaca Pada')),
                ('email_terkirim', models.BooleanField(default=False, verbose_name='Email Terkirim')),
                ('email_dikirim_pada', models.DateTimeField(blank=True, null=True, verbose_name='Email Dikirim Pada')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifikasi',
                    to='accounts.personel',
                    verbose_name='Penerima',
                )),
            ],
            options={
                'verbose_name': 'Notifikasi',
                'verbose_name_plural': 'Notifikasi',
                'ordering': ['-dibuat_pada'],
            },
        ),
    ]
