import csv
from datetime import time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import Satker
from sprin.models import Sprin
from .models import RekorAbsensi

def _get_today_record(user):
    return RekorAbsensi.objects.filter(personel=user, tanggal=timezone.localdate()).first()


def _is_terlambat(record):
    if not record or not record.waktu_masuk:
        return False
    local_time = timezone.localtime(record.waktu_masuk).time()
    return record.status == 'hadir' and local_time > time(8, 0)


def _get_record_badge(record):
    if record.sprin_id:
        return 'Dinas Luar'
    if record.status == 'cuti':
        return 'Cuti'
    if record.status == 'izin':
        return 'Izin'
    if record.status == 'sakit':
        return 'Sakit'
    if _is_terlambat(record):
        return 'Terlambat'
    return record.get_status_display()


def _build_personal_stats(queryset):
    return {
        'total_hadir': queryset.filter(status='hadir', sprin__isnull=True).count(),
        'total_terlambat': queryset.filter(status='hadir', waktu_masuk__time__gt=time(8, 0), sprin__isnull=True).count(),
        'total_izin': queryset.filter(status__in=['izin', 'cuti']).count(),
        'total_dinas': queryset.filter(sprin__isnull=False).count(),
    }


def _build_rekap_admin_stats(queryset):
    return queryset.values(
        'personel__id',
        'personel__nrp',
        'personel__nama_lengkap',
        'personel__satker__nama',
    ).annotate(
        total_hadir=Count('id', filter=Q(status='hadir', sprin__isnull=True)),
        total_terlambat=Count('id', filter=Q(status='hadir', waktu_masuk__time__gt=time(8, 0), sprin__isnull=True)),
        total_izin=Count('id', filter=Q(status__in=['izin', 'cuti'])),
        total_dinas=Count('id', filter=Q(sprin__isnull=False)),
    ).order_by('personel__nama_lengkap')


def _export_personal_csv(queryset, filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    writer = csv.writer(response)

    writer.writerow(['Tanggal', 'Status', 'Check-In', 'Check-Out', 'Catatan', 'Sprin'])
    for record in queryset:
        writer.writerow([
            record.tanggal,
            _get_record_badge(record),
            timezone.localtime(record.waktu_masuk).strftime('%H:%M') if record.waktu_masuk else '-',
            timezone.localtime(record.waktu_keluar).strftime('%H:%M') if record.waktu_keluar else '-',
            record.catatan or '-',
            record.sprin.perihal if record.sprin_id else '-',
        ])

    return response


def _export_admin_csv(stats, filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    writer = csv.writer(response)

    writer.writerow(['NRP', 'Nama', 'Unit', 'Total Hadir', 'Total Terlambat', 'Total Izin / Cuti', 'Total Dinas'])
    for row in stats:
        writer.writerow([
            row['personel__nrp'],
            row['personel__nama_lengkap'],
            row['personel__satker__nama'] or '-',
            row['total_hadir'],
            row['total_terlambat'],
            row['total_izin'],
            row['total_dinas'],
        ])

    return response


@login_required
def dashboard_view(request):
    today_record = _get_today_record(request.user)
    recent_records = RekorAbsensi.objects.filter(personel=request.user).select_related('sprin').order_by('-tanggal', '-waktu_masuk')[:5]

    context = {
        'absensi': today_record,
        'sudah_checkin': bool(today_record and today_record.waktu_masuk),
        'sudah_checkout': bool(today_record and today_record.waktu_keluar),
        'label_hari_ini': _get_record_badge(today_record) if today_record else 'Belum Absen',
        'recent_records': recent_records,
        'is_terlambat_hari_ini': _is_terlambat(today_record),
    }
    return render(request, 'absensi/dashboard.html', context)


@login_required
def checkin_view(request):
    today = timezone.localdate()
    existing = RekorAbsensi.objects.filter(personel=request.user, tanggal=today).first()
    if existing and existing.waktu_masuk:
        messages.warning(request, 'Anda sudah melakukan check-in hari ini.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        lat = request.POST.get('lat') or request.POST.get('latitude')
        lon = request.POST.get('lon') or request.POST.get('longitude')
        foto = request.FILES.get('foto') or request.FILES.get('selfie_masuk')
        sprin_id = request.POST.get('sprin_id')
        sprin = Sprin.objects.filter(pk=sprin_id).first() if sprin_id else None

        rekord, created = RekorAbsensi.objects.get_or_create(
            personel=request.user, tanggal=today, sprin=sprin
        )
        rekord.waktu_masuk = timezone.now()
        rekord.lat_masuk = lat
        rekord.lon_masuk = lon
        if foto:
            rekord.foto_masuk = foto
        rekord.catatan = request.POST.get('catatan', '')
        rekord.status = 'hadir'
        rekord.save()
        messages.success(request, 'Check-in berhasil dicatat.')
        return redirect('dashboard:index')

    # Ambil sprin aktif untuk personel ini
    from personel.models import Personel as PersonelLama
    personel_lama = PersonelLama.objects.filter(nip=request.user.nrp).first()
    
    sprin_aktif = None
    if personel_lama:
        now = timezone.now()
        sprin_aktif = Sprin.objects.filter(
            daftar_personel__personel=personel_lama, 
            status='Disetujui',
            start_date__lte=now,
            end_date__gte=now
        ).first()

    today_record = RekorAbsensi.objects.filter(personel=request.user, tanggal=today).first()
    return render(request, 'absensi/checkin.html', {
        'sprin_aktif': sprin_aktif,
        'absensi': today_record,
        'sudah_checkin': bool(today_record and today_record.waktu_masuk),
    })


@login_required
def checkout_view(request):
    today = timezone.localdate()
    rekord = RekorAbsensi.objects.filter(
        personel=request.user, tanggal=today, waktu_masuk__isnull=False
    ).first()
    if not rekord:
        messages.warning(request, 'Anda belum melakukan check-in hari ini.')
        return redirect('dashboard:index')
    if rekord.waktu_keluar:
        messages.warning(request, 'Anda sudah melakukan check-out hari ini.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        lat = request.POST.get('lat') or request.POST.get('latitude')
        lon = request.POST.get('lon') or request.POST.get('longitude')
        foto = request.FILES.get('foto') or request.FILES.get('selfie_keluar')
        rekord.waktu_keluar = timezone.now()
        rekord.lat_keluar = lat
        rekord.lon_keluar = lon
        if foto:
            rekord.foto_keluar = foto
        rekord.save()
        messages.success(request, 'Check-out berhasil dicatat.')
        return redirect('dashboard:index')

    return render(request, 'absensi/checkout.html', {'absensi': rekord})


@login_required
def history_view(request):
    records = RekorAbsensi.objects.filter(personel=request.user).select_related('sprin').order_by('-tanggal', '-waktu_masuk')
    for record in records:
        record.status_badge = _get_record_badge(record)

    return render(request, 'absensi/history.html', {'records': records})


@login_required
def rekap_pribadi_view(request):
    today = timezone.localdate()
    date_from = request.GET.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', today.strftime('%Y-%m-%d'))

    records = RekorAbsensi.objects.filter(
        personel=request.user,
        tanggal__range=[date_from, date_to],
    ).select_related('sprin').order_by('-tanggal', '-waktu_masuk')

    if request.GET.get('export') == 'csv':
        return _export_personal_csv(records, f"Rekap_Pribadi_{request.user.nrp}_{date_from}_to_{date_to}")

    for record in records:
        record.status_badge = _get_record_badge(record)
        record.terlambat = _is_terlambat(record)

    context = {
        'records': records,
        'stats': _build_personal_stats(records),
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'absensi/rekap_pribadi.html', context)


@login_required
def rekap_admin_view(request):
    if request.user.role not in ['superadmin', 'operator', 'pimpinan']:
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard:index')

    today = timezone.localdate()
    date_from = request.GET.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', today.strftime('%Y-%m-%d'))
    satker_id = request.GET.get('satker')
    search = request.GET.get('q', '')

    records = RekorAbsensi.objects.filter(
        tanggal__range=[date_from, date_to],
        personel__is_active=True,
    ).select_related('personel', 'personel__satker', 'sprin')

    if satker_id:
        records = records.filter(personel__satker_id=satker_id)
    if search:
        records = records.filter(
            Q(personel__nama_lengkap__icontains=search) |
            Q(personel__nrp__icontains=search)
        )

    stats = _build_rekap_admin_stats(records)

    if request.GET.get('export') == 'csv':
        return _export_admin_csv(stats, f"Rekap_Absensi_{date_from}_to_{date_to}")

    context = {
        'stats': stats,
        'date_from': date_from,
        'date_to': date_to,
        'satkers': Satker.objects.all(),
        'selected_satker': int(satker_id) if satker_id and satker_id.isdigit() else '',
        'search': search,
    }
    return render(request, 'absensi/rekap_admin.html', context)
