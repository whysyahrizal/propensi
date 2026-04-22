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
        sprin_aktif = Sprin.objects.filter(status='aktif')
        total_personel = request.user.__class__.objects.filter(is_active=True, role='personel').count()
        hadir_hari_ini = RekorAbsensi.objects.filter(tanggal=today).count()

        return render(request, 'dashboard/index.html', {
            'sprin_aktif': sprin_aktif,
            'total_personel': total_personel,
            'hadir_hari_ini': hadir_hari_ini,
            'today': today,
        })
    else:
        # Cari profil Personel (personel.Personel) berdasarkan NRP user yang login
        from personel.models import Personel as PersonelProfile
        try:
            personel_profile = PersonelProfile.objects.get(nip=request.user.nrp)
        except PersonelProfile.DoesNotExist:
            personel_profile = None

        absensi_hari_ini = RekorAbsensi.objects.filter(
            personel=request.user, tanggal=today
        ).first()
        sprin_aktif_saya = None
        if personel_profile:
            sprin_aktif_saya = Sprin.objects.filter(
                daftar_personel__personel=personel_profile, status='aktif'
            ).first()

        return render(request, 'dashboard/index.html', {
            'absensi_hari_ini': absensi_hari_ini,
            'sprin_aktif_saya': sprin_aktif_saya,
            'today': today,
        })
