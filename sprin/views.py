from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from accounts.models import Personel
from locations.models import Location
from .models import Sprin, PersonelSprin


def _active_location_queryset():
    return Location.objects.filter(is_active=True).order_by('name')


def get_user_role(request):
    role = request.session.get('user_role', 'Operator')
    if role not in ['Operator', 'SDM', 'Pimpinan']:
        role = 'Operator'
    return role


@login_required
def create_sprin(request):
    if getattr(request.user, 'role', None) not in ('superadmin', 'operator', 'pimpinan'):
        messages.error(request, "Akses ditolak.")
        return redirect('dashboard:index')

    personel_all = Personel.objects.filter(is_active=True).order_by('nama_lengkap')
    personel_staff = personel_all.filter(role__in=['operator', 'superadmin'])
    personel_pimpinan = personel_all.filter(role='pimpinan')
    personel_terlibat = personel_all.filter(role='personel')
    active_locations = _active_location_queryset()

    if request.method == 'POST':
        location_id = request.POST.get('location_id')
        selected_location = active_locations.filter(pk=location_id).first()
        if not selected_location:
            messages.error(request, "Lokasi penugasan wajib dipilih dari daftar wilayah aktif.")
            return render(request, 'sprin/create_sprin.html', {
                'personel_all': personel_all,
                'personel_staff': personel_staff,
                'personel_pimpinan': personel_pimpinan,
                'personel_terlibat': personel_terlibat,
                'active_locations': active_locations,
                'selected_location_id': location_id,
            })

        # Simpan data utama
        sprin = Sprin.objects.create(
            operation_name=request.POST.get('operation_name'),
            description=request.POST.get('description'),
            location_name=f'{selected_location.name} ({selected_location.get_type_display()})',
            # latitude=request.POST.get('latitude'),
            # longitude=request.POST.get('longitude'),
            # radius_meter=request.POST.get('radius_meter', 100),
            created_by_id=request.POST.get('created_by'),
            approved_by_id=request.POST.get('approved_by'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
        )

        # Simpan list personel yang ditugaskan
        personel_ids = request.POST.getlist('personel_ids[]')
        for p_id in personel_ids:
            if p_id: 
                PersonelSprin.objects.create(sprin=sprin, personel_id=p_id)
        
        messages.success(request, "Sprin baru berhasil diterbitkan otomatis!")
        return redirect('sprin:daftar')

    return render(request, 'sprin/create_sprin.html', {
        'personel_all': personel_all,
        'personel_staff': personel_staff,
        'personel_pimpinan': personel_pimpinan,
        'personel_terlibat': personel_terlibat,
        'active_locations': active_locations,
        'selected_location_id': '',
    })

def all_sprin(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', 'all')

    list_sprin = Sprin.objects.all().order_by('-created_at')
    if status == 'pending':
        list_sprin = list_sprin.filter(status='Menunggu Persetujuan')
    elif status == 'disetujui':
        list_sprin = list_sprin.filter(status='Disetujui')

    if q:
        list_sprin = list_sprin.filter(
            Q(operation_name__icontains=q) |
            Q(description__icontains=q) |
            Q(location_name__icontains=q)
        )

    return render(request, 'sprin/all_sprin.html', {
        'list_sprin': list_sprin,
        'page_type': status,
        'q': q,
        'status': status,
        'active_nav': 'sprin'
    })

from django.shortcuts import render, redirect, get_object_or_404
from .models import Sprin, PersonelSprin

# 1. List Khusus Pimpinan (Hanya yang belum disetujui)
def pimpinan_list(request):
    q = request.GET.get('q', '').strip()
    list_pending = Sprin.objects.filter(status='Menunggu Persetujuan').order_by('-created_at')
    if q:
        list_pending = list_pending.filter(
            Q(operation_name__icontains=q) |
            Q(description__icontains=q) |
            Q(location_name__icontains=q)
        )
    return render(request, 'sprin/all_sprin.html', {
        'list_sprin': list_pending,
        'page_type': 'pending',
        'q': q,
        'status': 'pending',
        'active_nav': 'sprin'
    })

# 2. Detail Sprin (Bisa dipakai Umum & Pimpinan)
def detail_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    personel_tugas = PersonelSprin.objects.filter(sprin=sprin)
    role = get_user_role(request)

    return render(request, 'sprin/detail_sprin.html', {
        'sprin': sprin,
        'personel_tugas': personel_tugas,
        'user_role': role,
        'active_nav': 'sprin'
    })


def aksi_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    role = get_user_role(request)
    if role != 'Pimpinan':
        messages.error(request, "Hanya user Pimpinan yang boleh melakukan aksi ini.")
        return redirect('sprin:detail_sprin', pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'setujui':
            sprin.status = 'Disetujui'
            sprin.rejection_notes = None
            sprin.save()
            messages.success(request, "Sprin disetujui. Admin SDM sekarang dapat mengunggah file.")
            return redirect('sprin:detail_sprin', pk=pk)

        if action == 'tolak':
            reject_notes = request.POST.get('reject_notes', '').strip()
            if not reject_notes:
                messages.error(request, "Alasan penolakan wajib diisi.")
                return redirect('sprin:detail_sprin', pk=pk)
            sprin.status = 'Ditolak'
            sprin.rejection_notes = reject_notes
            sprin.file_surat = None
            sprin.save()
            messages.success(request, "Sprin ditolak dengan catatan.")
            return redirect('sprin:detail_sprin', pk=pk)

    return redirect('sprin:detail_sprin', pk=pk)


def disetujui_list(request):
    q = request.GET.get('q', '').strip()
    list_sprin = Sprin.objects.filter(status='Disetujui').order_by('-created_at')
    if q:
        list_sprin = list_sprin.filter(
            Q(operation_name__icontains=q) |
            Q(description__icontains=q) |
            Q(location_name__icontains=q)
        )
    return render(request, 'sprin/all_sprin.html', {
        'list_sprin': list_sprin,
        'page_type': 'disetujui',
        'q': q,
        'status': 'disetujui',
        'active_nav': 'sprin'
    })


def set_role(request):
    role = request.GET.get('role', 'Operator')
    if role not in ['Operator', 'SDM', 'Pimpinan']:
        role = 'Operator'
    request.session['user_role'] = role
    messages.success(request, f"Role sekarang: {role}")
    return redirect(request.META.get('HTTP_REFERER', '/sprin/'))


def upload_file_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    role = get_user_role(request)
    if role != 'SDM':
        messages.error(request, "Hanya user SDM yang boleh mengunggah file.")
        return redirect('sprin:detail_sprin', pk=pk)

    if request.method == 'POST':
        if sprin.status != 'Disetujui':
            messages.error(request, "Hanya sprin yang disetujui dapat mengunggah file.")
        elif 'file_surat' not in request.FILES:
            messages.error(request, "Tidak ada file yang dipilih untuk diunggah.")
        else:
            sprin.file_surat = request.FILES['file_surat']
            sprin.save()
            messages.success(request, "File PDF berhasil diunggah.")
    return redirect('sprin:detail_sprin', pk=pk)