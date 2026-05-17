from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime, time, timedelta
import json

from absensi.models import RekorAbsensi
from accounts.models import Personel, Satker
from manajemen_cuti.models import PengajuanCuti
from pengumuman.models import Pengumuman
from schedules.models import ShiftSchedulePersonnel
from sprin.models import PersonelSprin, Sprin


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

@login_required
def superadmin_dashboard_view(request):
    if getattr(request.user, 'role', '') != 'superadmin' and not request.user.is_superuser:
        raise PermissionDenied  

    filter_type = request.GET.get('filter', 'hari_ini')
    today = timezone.localtime().date()
    
    if filter_type == '7_hari':
        start_date = today - timedelta(days=6)
        end_date = today
    elif filter_type == 'bulan_ini':
        start_date = today.replace(day=1)
        end_date = today
    elif filter_type == 'kustom':
        start_date = datetime.strptime(request.GET.get('start_date', ''), '%Y-%m-%d').date() if request.GET.get('start_date') else today
        end_date = datetime.strptime(request.GET.get('end_date', ''), '%Y-%m-%d').date() if request.GET.get('end_date') else today
    else:
        start_date = today
        end_date = today

    delta_days = (end_date - start_date).days + 1

    personel_aktif = Personel.objects.filter(is_active=True, status_verifikasi='approved')
    total_personel = personel_aktif.count()
    total_potensi_hadir = total_personel * delta_days
    
    absensi_qs = RekorAbsensi.objects.filter(tanggal__range=[start_date, end_date], waktu_masuk__isnull=False)
    total_hadir = absensi_qs.count()
    
    hadir_terlambat = sum(1 for a in absensi_qs if timezone.localtime(a.waktu_masuk).time() > time(7, 0, 59))
    total_tidak_hadir = max(0, total_potensi_hadir - total_hadir)
    tingkat_kehadiran = (total_hadir / total_potensi_hadir * 100) if total_potensi_hadir > 0 else 0

    trend_labels, trend_hadir, trend_tidak_hadir = [], [], []
    for i in range(6, -1, -1):
        loop_date = today - timedelta(days=i)
        trend_labels.append(loop_date.strftime('%d %b'))
        h_count = RekorAbsensi.objects.filter(tanggal=loop_date, waktu_masuk__isnull=False).count()
        trend_hadir.append(h_count)
        trend_tidak_hadir.append(max(0, total_personel - h_count))

    donut_data = [total_hadir - hadir_terlambat, hadir_terlambat, total_tidak_hadir]

    bar_labels, bar_satker_ids, bar_kinerja = [], [], []
    satkers = Satker.objects.all().order_by('nama')
    for s in satkers:
        p_count = personel_aktif.filter(satker=s).count()
        if p_count == 0: continue
        h_unit = absensi_base = RekorAbsensi.objects.filter(tanggal__range=[start_date, end_date], personel__satker=s, waktu_masuk__isnull=False).count()
        potensi_unit = p_count * delta_days
        rate = (h_unit / potensi_unit * 100) if potensi_unit > 0 else 0
        bar_labels.append(s.nama)
        bar_satker_ids.append(s.id)
        bar_kinerja.append(round(rate, 1))

    context = {
        'filter_type': filter_type, 'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d'),
        'total_personel': total_personel, 'total_hadir': total_hadir, 'total_tidak_hadir': total_tidak_hadir, 'total_terlambat': hadir_terlambat, 'tingkat_kehadiran': round(tingkat_kehadiran, 1),
        'trend_labels': json.dumps(trend_labels), 'trend_hadir': json.dumps(trend_hadir), 'trend_tidak_hadir': json.dumps(trend_tidak_hadir), 'donut_data': json.dumps(donut_data),
        'bar_labels': json.dumps(bar_labels), 'bar_satker_ids': json.dumps(bar_satker_ids), 'bar_kinerja': json.dumps(bar_kinerja),
    }
    return render(request, 'dashboard/dashboard_kehadiran_superadmin.html', context)


@login_required
def superadmin_unit_detail_view(request):
    if getattr(request.user, 'role', '') != 'superadmin' and not request.user.is_superuser:
        raise PermissionDenied  

    satker_id = request.GET.get('satker_id')
    if not satker_id:
        return redirect('dashboard:dashboard_kehadiran_superadmin')
    satker = get_object_or_404(Satker, pk=satker_id)

    filter_type = request.GET.get('filter', 'hari_ini')
    today = timezone.localtime().date()
    
    if filter_type == '7_hari':
        start_date = today - timedelta(days=6)
        end_date = today
    elif filter_type == 'bulan_ini':
        start_date = today.replace(day=1)
        end_date = today
    elif filter_type == 'kustom':
        start_date = datetime.strptime(request.GET.get('start_date', ''), '%Y-%m-%d').date() if request.GET.get('start_date') else today
        end_date = datetime.strptime(request.GET.get('end_date', ''), '%Y-%m-%d').date() if request.GET.get('end_date') else today
    else:
        start_date = today
        end_date = today

    delta_days = (end_date - start_date).days + 1
    personel_list = Personel.objects.filter(satker=satker, is_active=True, status_verifikasi='approved').order_by('nama_lengkap')
    total_personel = personel_list.count()
    total_potensi = total_personel * delta_days

    absensi_unit_qs = RekorAbsensi.objects.filter(tanggal__range=[start_date, end_date], personel__satker=satker)
    total_hadir = absensi_unit_qs.count()
    terlambat = sum(1 for a in absensi_unit_qs if timezone.localtime(a.waktu_masuk).time() > time(7, 0, 59))
    tidak_hadir = max(0, total_potensi - total_hadir)

    kinerja_personel = []
    for p in personel_list:
        p_abs = absensi_unit_qs.filter(personel=p)
        h_c = p_abs.count()
        t_c = sum(1 for a in p_abs if timezone.localtime(a.waktu_masuk).time() > time(7, 0, 59))
        th_c = max(0, delta_days - h_c)
        rate = (h_c / delta_days * 100) if delta_days > 0 else 0
        kinerja_personel.append({
            'personel': p, 'hadir': h_c, 'terlambat': t_c, 'tidak_hadir': th_c, 'persentase': round(rate, 1)
        })

    context = {
        'satker': satker, 'filter_type': filter_type, 'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d'),
        'total_personel': total_personel, 'total_hadir': total_hadir, 'total_tidak_hadir': tidak_hadir, 'total_terlambat': terlambat, 'kinerja_personel': kinerja_personel,
    }
    return render(request, 'dashboard/dashboard_kehadiran_unit.html', context)


@login_required
def pimpinan_dashboard_view(request):
    if getattr(request.user, 'role', '') != 'pimpinan':
        raise PermissionDenied  

    satker = request.user.satker
    if not satker:
        raise PermissionDenied("Akun Pimpinan Anda belum terhubung dengan Satuan Kerja.")

    filter_type = request.GET.get('filter', 'hari_ini')
    today = timezone.localtime().date()
    
    if filter_type == '7_hari':
        start_date = today - timedelta(days=6)
        end_date = today
    elif filter_type == 'bulan_ini':
        start_date = today.replace(day=1)
        end_date = today
    elif filter_type == 'kustom':
        start_date = datetime.strptime(request.GET.get('start_date', ''), '%Y-%m-%d').date() if request.GET.get('start_date') else today
        end_date = datetime.strptime(request.GET.get('end_date', ''), '%Y-%m-%d').date() if request.GET.get('end_date') else today
    else:
        start_date = today
        end_date = today

    delta_days = (end_date - start_date).days + 1
    personel_list = Personel.objects.filter(satker=satker, is_active=True, status_verifikasi='approved').order_by('nama_lengkap')
    total_personel = personel_list.count()
    total_potensi = total_personel * delta_days

    absensi_unit_qs = RekorAbsensi.objects.filter(tanggal__range=[start_date, end_date], personel__satker=satker)
    total_hadir = absensi_unit_qs.count()
    terlambat = sum(1 for a in absensi_unit_qs if timezone.localtime(a.waktu_masuk).time() > time(7, 0, 59))
    tidak_hadir = max(0, total_potensi - total_hadir)
    tingkat_kehadiran = (total_hadir / total_potensi * 100) if total_potensi > 0 else 0

    trend_labels, trend_hadir, trend_tidak_hadir = [], [], []
    for i in range(6, -1, -1):
        loop_date = today - timedelta(days=i)
        trend_labels.append(loop_date.strftime('%d %b'))
        h_c = RekorAbsensi.objects.filter(tanggal=loop_date, personel__satker=satker, waktu_masuk__isnull=False).count()
        trend_hadir.append(h_c)
        trend_tidak_hadir.append(max(0, total_personel - h_c))

    donut_data = [total_hadir - terlambat, terlambat, tidak_hadir]

    kinerja_personel = []
    for p in personel_list:
        p_abs = absensi_unit_qs.filter(personel=p)
        h_c = p_abs.count()
        t_c = sum(1 for a in p_abs if timezone.localtime(a.waktu_masuk).time() > time(7, 0, 59))
        th_c = max(0, delta_days - h_c)
        rate = (h_c / delta_days * 100) if delta_days > 0 else 0
        kinerja_personel.append({
            'personel': p, 'hadir': h_c, 'terlambat': t_c, 'tidak_hadir': th_c, 'persentase': round(rate, 1)
        })

    context = {
        'satker': satker, 'filter_type': filter_type, 'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d'),
        'total_personel': total_personel, 'total_hadir': total_hadir, 'total_tidak_hadir': tidak_hadir, 'total_terlambat': terlambat, 'tingkat_kehadiran': round(tingkat_kehadiran, 1),
        'trend_labels': json.dumps(trend_labels), 'trend_hadir': json.dumps(trend_hadir), 'trend_tidak_hadir': json.dumps(trend_tidak_hadir), 'donut_data': json.dumps(donut_data), 'kinerja_personel': kinerja_personel,
    }
    return render(request, 'dashboard/dashboard_kehadiran_pimpinan.html', context)


# ==============================================================================
# 4. MONITORING KEHADIRAN SPRIN — HALAMAN UTAMA
# ==============================================================================
@login_required
def monitoring_sprin_main_view(request):
    role = getattr(request.user, 'role', '')
    if role not in ['superadmin', 'pimpinan'] and not request.user.is_superuser:
        raise PermissionDenied

    # Ambil parameter filter
    search_query = request.GET.get('q', '')
    lokasi_filter = request.GET.get('lokasi', '')
    satker_id = request.GET.get('satker_id', '')
    bulan_filter = request.GET.get('bulan', '4') # Default contoh: April

    today = timezone.localtime().date()
    now = timezone.now()

    # Query dasar: semua Sprin yang disetujui
    sprin_qs = Sprin.objects.filter(status='Disetujui')

    # Filter berdasarkan hak akses Role
    if role == 'pimpinan':
        satker = request.user.satker
        if not satker:
            raise PermissionDenied("Akun pimpinan Anda belum dikaitkan dengan Satuan Kerja.")
        sprin_qs = sprin_qs.filter(daftar_personel__personel__satker=satker).distinct()
        satkers = []
    else:
        satkers = Satker.objects.all().order_by('nama')
        if satker_id:
            sprin_qs = sprin_qs.filter(daftar_personel__personel__satker_id=satker_id).distinct()

    # Filter pencarian & dropdown dinamis
    if search_query:
        sprin_qs = sprin_qs.filter(operation_name__icontains=search_query) | sprin_qs.filter(id_sprin__icontains=search_query)
    if lokasi_filter:
        sprin_qs = sprin_qs.filter(location_name__icontains=lokasi_filter)
    if bulan_filter:
        sprin_qs = sprin_qs.filter(start_date__month=bulan_filter)

    # Proses kalkulasi data rekapitulasi untuk tabel & chart
    sprin_list_data = []
    total_personel_nasional = 0
    total_sudah_absen_nasional = 0
    total_belum_absen_nasional = 0
    
    sprin_lengkap_count = 0
    perlu_perhatian_count = 0
    total_persentase_kumulatif = 0

    for s in sprin_qs:
        # Ambil relasi personel dinas di sprin ini
        p_sprin_qs = PersonelSprin.objects.filter(sprin=s)
        if role == 'pimpinan':
            p_sprin_qs = p_sprin_qs.filter(personel__satker=request.user.satker)

        total_p = p_sprin_qs.count()
        if total_p == 0:
            continue

        # Hitung jumlah absen hari ini untuk personel di sprin tersebut
        personel_ids = p_sprin_qs.values_list('personel_id', flat=True)
        sudah_absen = RekorAbsensi.objects.filter(tanggal=today, personel_id__in=personel_ids, waktu_masuk__isnull=False).count()
        belum_absen = max(0, total_p - sudah_absen)

        # Hitung kelengkapan %
        persentase = round((sudah_absen / total_p * 100), 1) if total_p > 0 else 0
        total_persentase_kumulatif += persentase

        if persentase >= 90:
            status_kelengkapan = "Lengkap"
            sprin_lengkap_count += 1
        elif persentase >= 60:
            status_kelengkapan = "Sebagian"
        else:
            status_kelengkapan = "Rendah"
            perlu_perhatian_count += 1

        sprin_list_data.append({
            'sprin': s,
            'total_personel': total_p,
            'sudah_absen': sudah_absen,
            'belum_absen': belum_absen,
            'persentase': persentase,
            'status_kelengkapan': status_kelengkapan
        })

        # Akumulasi KPI Cards global
        total_personel_nasional += total_p
        total_sudah_absen_nasional += sudah_absen
        total_belum_absen_nasional += belum_absen

    total_sprin_aktif = len(sprin_list_data)
    rata_rata_kelengkapan = round(total_persentase_kumulatif / total_sprin_aktif, 1) if total_sprin_aktif > 0 else 0
    tingkat_kehadiran_global = round((total_sudah_absen_nasional / total_personel_nasional * 100), 1) if total_personel_nasional > 0 else 0

    # Ambil list lokasi unik untuk dropdown filter
    lokasi_list = Sprin.objects.values_list('location_name', flat=True).distinct()

    context = {
        'role': role,
        'satkers': satkers,
        'lokasi_list': lokasi_list,
        'q': search_query,
        'selected_lokasi': lokasi_filter,
        'selected_satker': satker_id,
        'selected_bulan': bulan_filter,
        
        # 5 KPI Utama
        'total_sprin_aktif': total_sprin_aktif,
        'total_personel': total_personel_nasional,
        'sudah_absen': total_sudah_absen_nasional,
        'belum_absen': total_belum_absen_nasional,
        'tingkat_kehadiran': tingkat_kehadiran_global,

        # Sidebar Ringkasan Kanan
        'sprin_lengkap_count': sprin_lengkap_count,
        'perlu_perhatian_count': perlu_perhatian_count,
        'rata_rata_kelengkapan': rata_rata_kelengkapan,
        'donut_data': json.dumps([total_sudah_absen_nasional, total_belum_absen_nasional]),

        'sprin_list_data': sprin_list_data,
    }
    return render(request, 'dashboard/dashboard_sprin_main.html', context)


# ==============================================================================
# 5. MONITORING KEHADIRAN SPRIN — HALAMAN DETAIL
# ==============================================================================
@login_required
def monitoring_sprin_detail_view(request, sprin_id):
    role = getattr(request.user, 'role', '')
    if role not in ['superadmin', 'pimpinan'] and not request.user.is_superuser:
        raise PermissionDenied

    sprin = get_object_or_404(Sprin, pk=sprin_id)
    today = timezone.localtime().date()

    # Base Query Anggota terdaftar di Sprin ini
    p_sprin_base = PersonelSprin.objects.filter(sprin=sprin).select_related('personel', 'personel__satker')

    if role == 'pimpinan':
        satker = request.user.satker
        p_sprin_base = p_sprin_base.filter(personel__satker=satker)

    total_personel = p_sprin_base.count()

    # Hitung Log absensi harian di dalam penugasan lapangan
    personel_data_list = []
    sudah_absen_count = 0

    for ps in p_sprin_base:
        absensi = RekorAbsensi.objects.filter(tanggal=today, personel=ps.personel).first()
        
        if absensi and absensi.waktu_masuk:
            status_presensi = "Sudah Absen"
            waktu_presensi = timezone.localtime(absensi.waktu_masuk).strftime('%H:%M WIB')
            sudah_absen_count += 1
        else:
            status_presensi = "Belum Absen"
            waktu_presensi = "-"

        personel_data_list.append({
            'personel': ps.personel,
            'status_presensi': status_presensi,
            'waktu_presensi': waktu_presensi,
        })

    belum_absen_count = max(0, total_personel - sudah_absen_count)
    persentase_kehadiran = round((sudah_absen_count / total_personel * 100), 1) if total_personel > 0 else 0

    context = {
        'sprin': sprin,
        'total_personel': total_personel,
        'sudah_absen_count': sudah_absen_count,
        'belum_absen_count': belum_absen_count,
        'persentase_kehadiran': persentase_kehadiran,
        'personel_data_list': personel_data_list,
    }
    return render(request, 'dashboard/dashboard_sprin_detail.html', context)