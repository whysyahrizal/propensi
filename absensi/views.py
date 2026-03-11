from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import RekorAbsensi
from sprin.models import Sprin




@login_required
def checkin_view(request):
    today = timezone.localdate()
    existing = RekorAbsensi.objects.filter(personel=request.user, tanggal=today).first()
    if existing and existing.waktu_masuk:
        messages.warning(request, 'Anda sudah melakukan check-in hari ini.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        foto = request.FILES.get('foto')
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
        rekord.status = 'hadir'
        rekord.save()
        messages.success(request, 'Check-in berhasil dicatat.')
        return redirect('dashboard:index')

    # Ambil sprin aktif untuk personel ini
    sprin_aktif = Sprin.objects.filter(
        personel_list__personel=request.user, status='aktif'
    ).first()
    return render(request, 'absensi/checkin.html', {'sprin_aktif': sprin_aktif})


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
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        foto = request.FILES.get('foto')
        rekord.waktu_keluar = timezone.now()
        rekord.lat_keluar = lat
        rekord.lon_keluar = lon
        if foto:
            rekord.foto_keluar = foto
        rekord.save()
        messages.success(request, 'Check-out berhasil dicatat.')
        return redirect('dashboard:index')

    return render(request, 'absensi/checkout.html', {'rekord': rekord})
