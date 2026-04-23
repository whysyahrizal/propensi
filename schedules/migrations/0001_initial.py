from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('locations', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='ShiftSchedule',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('date', models.DateField(verbose_name='Tanggal Jadwal')),
                        ('shift_type', models.CharField(choices=[('pagi', 'Pagi'), ('siang', 'Siang'), ('malam', 'Malam')], max_length=10, verbose_name='Jenis Shift')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='schedules_created', to=settings.AUTH_USER_MODEL, verbose_name='Dibuat Oleh')),
                        ('location', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='schedules', to='locations.location', verbose_name='Lokasi Penugasan')),
                    ],
                    options={
                        'verbose_name': 'Jadwal Shift',
                        'verbose_name_plural': 'Jadwal Shift',
                        'ordering': ['date', 'shift_type', 'location__name'],
                        'db_table': 'dashboard_shiftschedule',
                        'unique_together': {('date', 'shift_type', 'location')},
                    },
                ),
                migrations.CreateModel(
                    name='ShiftSchedulePersonnel',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('personel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_shifts', to=settings.AUTH_USER_MODEL, verbose_name='Personel')),
                        ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='personnel_assignments', to='schedules.shiftschedule', verbose_name='Jadwal')),
                    ],
                    options={
                        'verbose_name': 'Personel Jadwal Shift',
                        'verbose_name_plural': 'Personel Jadwal Shift',
                        'ordering': ['personel__nama_lengkap'],
                        'db_table': 'dashboard_shiftschedulepersonnel',
                        'unique_together': {('schedule', 'personel')},
                    },
                ),
            ],
        ),
    ]
