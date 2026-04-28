# Avoid reverse accessor clash with manajemen_cuti.PengajuanCuti
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cuti", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pengajuancuti",
            name="disetujui_oleh",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cuti_persetujuan",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Diputuskan Oleh",
            ),
        ),
        migrations.AlterField(
            model_name="pengajuancuti",
            name="personel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cuti_pengajuan",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Personel",
            ),
        ),
    ]
