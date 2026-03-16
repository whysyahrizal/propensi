from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Presensi
from personel.models import Personel
from datetime import time

def _get_mobile_personel(request):
    personel_id = request.GET.get('personel_id') or request.POST.get('personel_id')
    if personel_id:
        try:
            return Personel.objects.filter(is_active=True).get(pk=personel_id)
        except (Personel.DoesNotExist, ValueError):
            pass
    
    if request.user.is_authenticated:
        personel = getattr(request.user, 'personel', None)
        if personel: return personel

    return Personel.objects.filter(is_active=True).first()

def presensi_dashboard(request):
    user_personel = _get_mobile_personel(request)
    today = timezone.now().date()
    now_time = timezone.now().time()
    
    presensi = Presensi.objects.filter(personel=user_personel, date=today).first()
    
    context = {
        'presensi': presensi,
        'can_checkin': False,
        'can_checkout': False,
        'status_msg': "Belum Presensi",
        'selected_personel': user_personel,
        'personel_list': Personel.objects.filter(is_active=True),
        'now': timezone.now()
    }

    if not presensi:
        context['can_checkin'] = True
    else:
        if presensi.type == 'Izin':
            context['status_msg'] = f"Izin: {presensi.izin_detail}"
        elif presensi.checkin_time and not presensi.checkout_time:
            context['status_msg'] = f"Check-in: {presensi.checkin_time.strftime('%H:%M')}"
            context['can_checkout'] = True
        elif presensi.checkout_time:
            context['status_msg'] = "Presensi Selesai"

    return render(request, 'presensi/dashboard.html', context)

def checkin_process(request):
    user_personel = _get_mobile_personel(request)
    if request.method == 'POST':
        is_within_radius = request.POST.get('is_within_radius') == 'true'
        p_type = request.POST.get('type')

        if p_type != 'Izin' and not is_within_radius:
            messages.error(request, "Check-in ditolak! Di luar radius.")
            return redirect(f"/presensi/?personel_id={user_personel.id}")

        today = timezone.now().date()
        now_time = timezone.now().time()
        
        current_status = "Hadir"
        if p_type == 'Office Hour' and now_time > time(8, 0):
            current_status = "Terlambat"
        elif p_type == 'Izin':
            current_status = request.POST.get('izin_detail')
        elif p_type == 'Dinas':
            current_status = "Dinas"

        presensi, created = Presensi.objects.get_or_create(
            personel=user_personel, date=today,
            defaults={
                'type': p_type, 'checkin_time': now_time,
                'checkin_photo': request.FILES.get('checkin_photo'),
                'supporting_document': request.FILES.get('supporting_document'),
                'izin_detail': request.POST.get('izin_detail'),
                'status': current_status
            }
        )
        messages.success(request, f"Check-in berhasil!")
        return redirect(f"/presensi/?personel_id={user_personel.id}")

    return render(request, 'presensi/checkin.html', {'selected_personel': user_personel})

def checkout_view(request):
    user_personel = _get_mobile_personel(request)
    today = timezone.now().date()
    presensi = Presensi.objects.filter(personel=user_personel, date=today).first()

    if not presensi or not presensi.checkin_time:
        messages.error(request, 'Belum ada check-in hari ini.')
        return redirect(f"/presensi/?personel_id={user_personel.id}")

    if request.method == 'POST':
        # Validasi Radius GPS
        if request.POST.get('is_within_radius') != 'true':
            messages.error(request, "Checkout ditolak! Lokasi tidak valid atau di luar radius.")
            return redirect(f"/presensi/?personel_id={user_personel.id}")

        now_time = timezone.now().time()
        presensi.checkout_time = now_time
        presensi.checkout_photo = request.FILES.get('checkout_photo')

        if presensi.type == 'Office Hour':
            # Jika status awalnya bukan Terlambat, maka otomatis Hadir
            if presensi.status != "Terlambat":
                presensi.status = "Hadir"
            # Jika status awalnya Terlambat, biarkan tetap Terlambat
        else:
            presensi.status = "Dinas"

        presensi.save()
        messages.success(request, "Checkout berhasil dicatat!")
        return redirect(f"/presensi/?personel_id={user_personel.id}")

    return render(request, 'presensi/checkout_form.html', {
        'selected_personel': user_personel, 
        'presensi': presensi
    })

def history(request):
    user_personel = _get_mobile_personel(request)
    records = Presensi.objects.filter(personel=user_personel).order_by('-date')
    return render(request, 'presensi/history.html', {
        'records': records, 'selected_personel': user_personel,
        'personel_list': Personel.objects.filter(is_active=True)
    })