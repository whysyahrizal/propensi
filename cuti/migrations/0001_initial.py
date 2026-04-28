import django.db.models.deletion
import cuti.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PengajuanCuti',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jenis_cuti', models.CharField(choices=[('tahunan', 'Cuti Tahunan'), ('sakit', 'Cuti Sakit'), ('bersalin', 'Cuti Bersalin'), ('alasan_penting', 'Cuti Alasan Penting'), ('besar', 'Cuti Besar'), ('luar_tanggungan', 'Cuti di Luar Tanggungan Negara'), ('izin', 'Izin')], max_length=20, verbose_name='Jenis Cuti')),
                ('tanggal_mulai', models.DateField(verbose_name='Tanggal Mulai')),
                ('tanggal_selesai', models.DateField(verbose_name='Tanggal Selesai')),
                ('alasan', models.TextField(verbose_name='Alasan Cuti')),
                ('lampiran', models.FileField(blank=True, null=True, upload_to=cuti.models.lampiran_cuti_path, verbose_name='Dokumen Pendukung')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=15, verbose_name='Status')),
                ('catatan_pimpinan', models.TextField(blank=True, verbose_name='Catatan Pimpinan')),
                ('disetujui_pada', models.DateTimeField(blank=True, null=True, verbose_name='Waktu Keputusan')),
                ('surat_cuti_final', models.FileField(blank=True, null=True, upload_to=cuti.models.surat_final_path, verbose_name='Surat Cuti Final')),
                ('dibuat_pada', models.DateTimeField(auto_now_add=True)),
                ('diperbarui_pada', models.DateTimeField(auto_now=True)),
                ('disetujui_oleh', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approval_cuti', to=settings.AUTH_USER_MODEL, verbose_name='Diputuskan Oleh')),
                ('personel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pengajuan_cuti', to=settings.AUTH_USER_MODEL, verbose_name='Personel')),
            ],
            options={
                'verbose_name': 'Pengajuan Cuti',
                'verbose_name_plural': 'Pengajuan Cuti',
                'ordering': ['-dibuat_pada'],
            },
        ),
    ]
