from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from absensi.models import RekorAbsensi
from cuti.models import PengajuanCuti
from pengumuman.models import Pengumuman
from schedules.models import ShiftSchedulePersonnel
from sprin.models import Sprin


def _published_pengumuman_queryset():
    return Pengumuman.objects.filter(is_active=True)


def _shift_time_label(shift_key):
    if shift_key == 'pagi':
        return '07:00 - 15:00 WIB'
    if shift_key == 'siang':
        return '15:00 - 23:00 WIB'
    return '23:00 - 07:00 WIB'


def _build_personal_timeline(user, today):
    assignments = (
        ShiftSchedulePersonnel.objects
        .filter(personel=user, schedule__date__gte=today)
        .select_related('schedule', 'schedule__location')
        .order_by('schedule__date', 'schedule__shift_type', 'schedule__location__name')[:30]
    )
    timeline = []
    for item in assignments:
        timeline.append({
            'tanggal': item.schedule.date,
            'shift_label': item.schedule.get_shift_type_display(),
            'shift_time': _shift_time_label(item.schedule.shift_type),
            'location': item.schedule.location.name,
            'status': 'Terjadwal',
        })
    return timeline


@login_required
def dashboard_view(request):
    today = timezone.localdate()
    role = request.user.role

    if role in ('pimpinan', 'superadmin', 'operator'):
        sprin_aktif = Sprin.objects.filter(status='aktif').select_related('dibuat_oleh')
        pengajuan_menunggu = PengajuanCuti.objects.filter(status='menunggu').count()
        total_personel = request.user.__class__.objects.filter(is_active=True, role='personel').count()
        hadir_hari_ini = RekorAbsensi.objects.filter(tanggal=today).count()
        pengumuman_terbaru = _published_pengumuman_queryset()[:5]

        return render(request, 'dashboard/index.html', {
            'sprin_aktif': sprin_aktif,
            'pengajuan_menunggu': pengajuan_menunggu,
            'total_personel': total_personel,
            'hadir_hari_ini': hadir_hari_ini,
            'pengumuman_terbaru': pengumuman_terbaru,
            'today': today,
        })

    absensi_hari_ini = RekorAbsensi.objects.filter(
        personel=request.user, tanggal=today
    ).first()
    sprin_aktif_saya = Sprin.objects.filter(
        daftar_personel__personel=request.user, status='aktif'
    ).first()
    cuti_terakhir = PengajuanCuti.objects.filter(
        personel=request.user
    ).first()
    pengumuman_terbaru = _published_pengumuman_queryset()[:5]

    upcoming_timeline = _build_personal_timeline(request.user, today)
    if upcoming_timeline:
        today_schedule = next((x for x in upcoming_timeline if x['tanggal'] == today), upcoming_timeline[0])
        jadwal_hari_ini = {
            'location': today_schedule['location'],
            'shift_label': today_schedule['shift_label'],
            'shift_time': today_schedule['shift_time'],
            'checkin_status': 'Belum Check-In' if not absensi_hari_ini else absensi_hari_ini.get_status_display(),
        }
    else:
        jadwal_hari_ini = {
            'location': 'Belum ada jadwal',
            'shift_label': '-',
            'shift_time': '-',
            'checkin_status': 'Belum Check-In' if not absensi_hari_ini else absensi_hari_ini.get_status_display(),
        }

    return render(request, 'dashboard/dashboard_personel.html', {
        'absensi_hari_ini': absensi_hari_ini,
        'sprin_aktif_saya': sprin_aktif_saya,
        'cuti_terakhir': cuti_terakhir,
        'pengumuman_terbaru': pengumuman_terbaru,
        'jadwal_hari_ini': jadwal_hari_ini,
        'jadwal_30_hari': upcoming_timeline,
        'today': today,
    })
