from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from absensi.models import RekorAbsensi
from manajemen_cuti.models import PengajuanCuti
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
        now = timezone.now()
        sprin_aktif = Sprin.objects.filter(
            status='Disetujui',
            start_date__lte=now,
            end_date__gte=now
        ).select_related('created_by')
        
        pengajuan_menunggu_qs = PengajuanCuti.objects.filter(status='pending')
        if role == 'pimpinan' and request.user.satker:
            pengajuan_menunggu_qs = pengajuan_menunggu_qs.filter(satuan_kerja=request.user.satker)
        pengajuan_menunggu = pengajuan_menunggu_qs.count()
        
        total_personel = request.user.__class__.objects.filter(is_active=True, status_verifikasi='approved', role='personel').count()
        hadir_hari_ini = RekorAbsensi.objects.filter(tanggal=today).count()
        
        # PBI-039 Revisi: Filter Cuti/Izin berdasarkan rentang tanggal
        from datetime import datetime
        cuti_dari_str = request.GET.get('cuti_dari') or today.strftime('%Y-%m-%d')
        cuti_sampai_str = request.GET.get('cuti_sampai') or today.strftime('%Y-%m-%d')
        
        try:
            cuti_dari_date = datetime.strptime(cuti_dari_str, '%Y-%m-%d').date()
        except ValueError:
            cuti_dari_date = today
            cuti_dari_str = today.strftime('%Y-%m-%d')
            
        try:
            cuti_sampai_date = datetime.strptime(cuti_sampai_str, '%Y-%m-%d').date()
        except ValueError:
            cuti_sampai_date = today
            cuti_sampai_str = today.strftime('%Y-%m-%d')

        cuti_izin_qs = PengajuanCuti.objects.filter(
            status='approved',
            tanggal_selesai__gte=cuti_dari_date,
            tanggal_mulai__lte=cuti_sampai_date
        ).select_related('personel', 'satuan_kerja')
        
        if role == 'pimpinan' and request.user.satker:
            cuti_izin_qs = cuti_izin_qs.filter(satuan_kerja=request.user.satker)
            
        sedang_cuti_izin = cuti_izin_qs.count()
        sedang_cuti_izin_list = cuti_izin_qs[:5]

        pengumuman_terbaru = _published_pengumuman_queryset()[:5]

        return render(request, 'dashboard/index.html', {
            'sprin_aktif': sprin_aktif,
            'pengajuan_menunggu': pengajuan_menunggu,
            'total_personel': total_personel,
            'hadir_hari_ini': hadir_hari_ini,
            'sedang_cuti_izin': sedang_cuti_izin,
            'sedang_cuti_izin_list': sedang_cuti_izin_list,
            'cuti_dari': cuti_dari_str,
            'cuti_sampai': cuti_sampai_str,
            'pengumuman_terbaru': pengumuman_terbaru,
            'today': today,
        })

    upcoming_timeline = _build_personal_timeline(request.user, today)
    if upcoming_timeline:
        today_schedule = next((x for x in upcoming_timeline if x['tanggal'] == today), upcoming_timeline[0])
        jadwal_hari_ini = {
            'location': today_schedule['location'],
            'shift_label': today_schedule['shift_label'],
            'shift_time': today_schedule['shift_time'],
        }
    else:
        jadwal_hari_ini = {
            'location': 'Belum ada jadwal',
            'shift_label': '-',
            'shift_time': '-',
        }

    return render(request, 'dashboard/dashboard_personel.html', {
        'jadwal_hari_ini': jadwal_hari_ini,
        'jadwal_30_hari': upcoming_timeline,
        'today': today,
    })


@login_required
def api_ringkasan_harian(request):
    now = timezone.now()
    today = timezone.localdate()
    
    # 1. Absensi
    absensi = RekorAbsensi.objects.filter(personel=request.user, tanggal=today).first()
    absensi_data = {
        'status': 'Sudah Absen' if absensi else 'Belum Absen',
        'waktu_masuk': absensi.waktu_masuk.strftime('%H:%M') if absensi and absensi.waktu_masuk else None,
        'waktu_keluar': absensi.waktu_keluar.strftime('%H:%M') if absensi and absensi.waktu_keluar else None,
    }

    # 2. Sprin Hari Ini
    sprin_hari_ini = Sprin.objects.filter(
        daftar_personel__personel=request.user,
        status='Disetujui',
        start_date__lte=now,
        end_date__gte=now
    ).first()
    
    sprin_data = {
        'ada': sprin_hari_ini is not None,
        'id': str(sprin_hari_ini.id_sprin) if sprin_hari_ini else None,
        'operation_name': sprin_hari_ini.operation_name if sprin_hari_ini else None,
        'location': sprin_hari_ini.location_name if sprin_hari_ini else None,
    }

    # 3. Jumlah Sprin Aktif
    jumlah_sprin_aktif = Sprin.objects.filter(
        daftar_personel__personel=request.user,
        status='Disetujui',
        start_date__lte=now,
        end_date__gte=now
    ).count()

    # 4. Sisa Cuti Tahunan
    current_year = today.year
    used_leave_queryset = PengajuanCuti.objects.filter(
        personel=request.user,
        jenis_cuti='tahunan',
        status='approved',
        tanggal_mulai__year=current_year
    )
    used_days = sum(cuti.durasi_hari for cuti in used_leave_queryset)
    sisa_cuti = max(0, 12 - used_days)

    return JsonResponse({
        'absensi': absensi_data,
        'sprin_hari_ini': sprin_data,
        'jumlah_sprin_aktif': jumlah_sprin_aktif,
        'sisa_cuti_tahunan': sisa_cuti
    })

@login_required
def api_informasi_aktivitas(request):
    from django.urls import reverse
    
    # 1. Pengumuman Terbaru
    pengumuman_qs = _published_pengumuman_queryset()[:5]
    pengumuman_list = [
        {
            'id': p.id,
            'judul': p.judul,
            'tanggal_publikasi': p.tanggal_publikasi.strftime('%d %b %Y'),
            'url': reverse('pengumuman:detail', args=[p.id])
        }
        for p in pengumuman_qs
    ]

    # 2. Aktivitas Terakhir
    absensi_terakhir = RekorAbsensi.objects.filter(
        personel=request.user, 
        waktu_masuk__isnull=False
    ).order_by('-waktu_masuk').first()
    
    cuti_terakhir = PengajuanCuti.objects.filter(
        personel=request.user
    ).order_by('-dibuat_pada').first()
    
    aktivitas = None
    
    absensi_time = absensi_terakhir.waktu_masuk if absensi_terakhir else None
    cuti_time = cuti_terakhir.dibuat_pada if cuti_terakhir else None
    
    if absensi_time and cuti_time:
        is_absensi_latest = absensi_time > cuti_time
    elif absensi_time:
        is_absensi_latest = True
    elif cuti_time:
        is_absensi_latest = False
    else:
        is_absensi_latest = None

    if is_absensi_latest is True:
        aktivitas = {
            'jenis': 'Absensi',
            'keterangan': f"Check-in berhasil",
            'tanggal': absensi_time.strftime('%d %b %Y'),
            'waktu': absensi_time.strftime('%H:%M WIB')
        }
    elif is_absensi_latest is False:
        aktivitas = {
            'jenis': 'Cuti/Izin',
            'keterangan': f"Pengajuan {cuti_terakhir.get_jenis_cuti_display()} {cuti_terakhir.get_status_display()}",
            'tanggal': cuti_time.strftime('%d %b %Y'),
            'waktu': cuti_time.strftime('%H:%M WIB')
        }

    return JsonResponse({
        'pengumuman': pengumuman_list,
        'aktivitas_terakhir': aktivitas
    })
