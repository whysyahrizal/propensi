from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from pengumuman.models import Pengumuman
from notifikasi.models import Notifikasi
from sprin.models import Sprin
from cuti.models import PengajuanCuti
from absensi.models import RekorAbsensi


@login_required
def dashboard_view(request):
    today = timezone.localdate()
    role = request.user.role

    if role in ('pimpinan', 'superadmin', 'operator'):
        # Dashboard Monitoring: statistik, sprin aktif, dsb.
        sprin_aktif = Sprin.objects.filter(status='aktif').select_related('dibuat_oleh')
        pengajuan_menunggu = PengajuanCuti.objects.filter(status='menunggu').count()
        total_personel = request.user.__class__.objects.filter(is_active=True, role='personel').count()
        hadir_hari_ini = RekorAbsensi.objects.filter(tanggal=today).count()
        pengumuman_terbaru = Pengumuman.objects.filter(is_published=True)[:5]

        return render(request, 'dashboard/dashboard_monitoring.html', {
            'sprin_aktif': sprin_aktif,
            'pengajuan_menunggu': pengajuan_menunggu,
            'total_personel': total_personel,
            'hadir_hari_ini': hadir_hari_ini,
            'pengumuman_terbaru': pengumuman_terbaru,
            'today': today,
        })
    else:
        # Dashboard Personel: status absensi hari ini, sprin, cuti, pengumuman
        absensi_hari_ini = RekorAbsensi.objects.filter(
            personel=request.user, tanggal=today
        ).first()
        sprin_aktif_saya = Sprin.objects.filter(
            personel_list__personel=request.user, status='aktif'
        ).first()
        cuti_terakhir = PengajuanCuti.objects.filter(
            personel=request.user
        ).first()
        pengumuman_terbaru = Pengumuman.objects.filter(is_published=True)[:5]

        return render(request, 'dashboard/dashboard_personel.html', {
            'absensi_hari_ini': absensi_hari_ini,
            'sprin_aktif_saya': sprin_aktif_saya,
            'cuti_terakhir': cuti_terakhir,
            'pengumuman_terbaru': pengumuman_terbaru,
            'today': today,
        })
