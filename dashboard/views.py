from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from sprin.models import Sprin
from absensi.models import RekorAbsensi


@login_required
def dashboard_view(request):
    today = timezone.localdate()
    role = request.user.role

    if role in ('pimpinan', 'superadmin', 'operator'):
        # Dashboard Monitoring — Sprint 2 (placeholder)
        sprin_aktif = Sprin.objects.filter(status='aktif').select_related('dibuat_oleh')
        total_personel = request.user.__class__.objects.filter(is_active=True, role='personel').count()
        hadir_hari_ini = RekorAbsensi.objects.filter(tanggal=today).count()

        return render(request, 'dashboard/index.html', {
            'sprin_aktif': sprin_aktif,
            'total_personel': total_personel,
            'hadir_hari_ini': hadir_hari_ini,
            'today': today,
        })
    else:
        # Dashboard Personel — Sprint 3 (placeholder)
        absensi_hari_ini = RekorAbsensi.objects.filter(
            personel=request.user, tanggal=today
        ).first()
        sprin_aktif_saya = Sprin.objects.filter(
            personel_list__personel=request.user, status='aktif'
        ).first()

        return render(request, 'dashboard/index.html', {
            'absensi_hari_ini': absensi_hari_ini,
            'sprin_aktif_saya': sprin_aktif_saya,
            'today': today,
        })
