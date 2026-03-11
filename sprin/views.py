from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Sprin, PersonelSprin
from accounts.models import Personel

ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _can_manage_sprin(user):
    """PBI-021/022/024: operator atau admin/superadmin"""
    return user.role in ('operator', 'superadmin')


def _can_approve_sprin(user):
    """PBI-026/027/028: pimpinan atau superadmin"""
    return user.role in ('pimpinan', 'superadmin')


def _validate_file(file):
    """PBI-021: validasi tipe dan ukuran lampiran"""
    if not file:
        return None
    import os
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f'Format file tidak diizinkan. Gunakan: {", ".join(ALLOWED_EXTENSIONS)}'
    if file.size > MAX_FILE_SIZE:
        return f'Ukuran file terlalu besar. Maksimal 10MB.'
    return None


# ─── PBI-024: Daftar Sprin (Operator/Admin) ─────────────────────────────────
@login_required
def daftar_sprin(request):
    role = request.user.role
    if role == 'personel':
        sprin_list = Sprin.objects.filter(
            personel_list__personel=request.user
        ).distinct().order_by('-tanggal')
    else:
        sprin_list = Sprin.objects.all().select_related('dibuat_oleh')

    # Filter status (PBI-024 & 026)
    filter_status = request.GET.get('status', '')
    if filter_status:
        sprin_list = sprin_list.filter(status=filter_status)

    # Filter periode
    filter_dari = request.GET.get('dari', '')
    filter_sampai = request.GET.get('sampai', '')
    if filter_dari:
        sprin_list = sprin_list.filter(tanggal__gte=filter_dari)
    if filter_sampai:
        sprin_list = sprin_list.filter(tanggal__lte=filter_sampai)

    # Search
    q = request.GET.get('q', '')
    if q:
        sprin_list = sprin_list.filter(
            Q(nomor__icontains=q) | Q(perihal__icontains=q) | Q(lokasi_penugasan__icontains=q)
        )

    return render(request, 'sprin/daftar_sprin.html', {
        'sprin_list': sprin_list,
        'filter_status': filter_status,
        'filter_dari': filter_dari,
        'filter_sampai': filter_sampai,
        'q': q,
        'total': sprin_list.count(),
        'STATUS_CHOICES': Sprin.STATUS_CHOICES,
        'can_manage': _can_manage_sprin(request.user),
        'can_approve': _can_approve_sprin(request.user),
    })


# ─── PBI-025/027: Detail Sprin ────────────────────────────────────────────────
@login_required
def detail_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    personel_sprin = sprin.personel_list.select_related('personel').all()
    semua_personel = Personel.objects.exclude(pk__in=[ps.personel_id for ps in personel_sprin])
    return render(request, 'sprin/detail_sprin.html', {
        'sprin': sprin,
        'personel_sprin': personel_sprin,
        'semua_personel': semua_personel,
        'can_manage': _can_manage_sprin(request.user),
        'can_approve': _can_approve_sprin(request.user),
    })


# ─── PBI-021: Tambah Sprin (Operator) ────────────────────────────────────────
@login_required
def tambah_sprin(request):
    if not _can_manage_sprin(request.user):
        messages.error(request, 'Hanya Operator atau Admin yang dapat membuat Sprin.')
        return redirect('sprin:daftar')

    if request.method == 'POST':
        nomor = request.POST.get('nomor', '').strip()
        tanggal = request.POST.get('tanggal', '').strip()
        perihal = request.POST.get('perihal', '').strip()

        # Validasi field wajib
        errors = []
        if not nomor:
            errors.append('Nomor Sprin wajib diisi.')
        if not tanggal:
            errors.append('Tanggal wajib diisi.')
        if not perihal:
            errors.append('Perihal wajib diisi.')
        if Sprin.objects.filter(nomor=nomor).exists():
            errors.append(f'Nomor Sprin "{nomor}" sudah digunakan.')

        # Validasi file lampiran
        file = request.FILES.get('file_sprin')
        file_error = _validate_file(file) if file else None
        if file_error:
            errors.append(file_error)

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'sprin/form_sprin.html', {
                'action': 'tambah',
                'form_data': request.POST,
            })

        sprin = Sprin.objects.create(
            nomor=nomor,
            tanggal=tanggal,
            perihal=perihal,
            dasar=request.POST.get('dasar', ''),
            isi_perintah=request.POST.get('isi_perintah', ''),
            lokasi_penugasan=request.POST.get('lokasi_penugasan', ''),
            waktu_mulai=request.POST.get('waktu_mulai') or None,
            waktu_selesai=request.POST.get('waktu_selesai') or None,
            dibuat_oleh=request.user,
            status='draft',
            file_sprin=file if file else None,
        )
        messages.success(request, f'Sprin {sprin.nomor} berhasil dibuat.')
        return redirect('sprin:detail', pk=sprin.pk)

    return render(request, 'sprin/form_sprin.html', {'action': 'tambah'})


# ─── PBI-022: Edit Sprin (Operator) ──────────────────────────────────────────
@login_required
def edit_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)

    if not _can_manage_sprin(request.user):
        messages.error(request, 'Hanya Operator atau Admin yang dapat mengedit Sprin.')
        return redirect('sprin:detail', pk=pk)

    # PBI-022: tidak bisa edit jika sudah approved/active
    if not sprin.dapat_diedit:
        messages.error(request, f'Sprin dengan status "{sprin.get_status_display()}" tidak dapat diedit.')
        return redirect('sprin:detail', pk=pk)

    if request.method == 'POST':
        nomor_baru = request.POST.get('nomor', sprin.nomor).strip()
        perihal = request.POST.get('perihal', sprin.perihal).strip()

        errors = []
        if not nomor_baru:
            errors.append('Nomor Sprin tidak boleh kosong.')
        if not perihal:
            errors.append('Perihal tidak boleh kosong.')
        # Cek duplikat nomor (kecuali dirinya sendiri)
        if Sprin.objects.filter(nomor=nomor_baru).exclude(pk=pk).exists():
            errors.append(f'Nomor Sprin "{nomor_baru}" sudah digunakan.')

        # Validasi file lampiran
        file = request.FILES.get('file_sprin')
        file_error = _validate_file(file) if file else None
        if file_error:
            errors.append(file_error)

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'sprin/form_sprin.html', {'sprin': sprin, 'action': 'edit'})

        sprin.nomor = nomor_baru
        sprin.tanggal = request.POST.get('tanggal', sprin.tanggal)
        sprin.perihal = perihal
        sprin.dasar = request.POST.get('dasar', sprin.dasar)
        sprin.isi_perintah = request.POST.get('isi_perintah', sprin.isi_perintah)
        sprin.lokasi_penugasan = request.POST.get('lokasi_penugasan', sprin.lokasi_penugasan)
        if request.POST.get('waktu_mulai'):
            sprin.waktu_mulai = request.POST['waktu_mulai']
        if request.POST.get('waktu_selesai'):
            sprin.waktu_selesai = request.POST['waktu_selesai']
        if file:
            sprin.file_sprin = file
        sprin.save()
        messages.success(request, 'Sprin berhasil diperbarui.')
        return redirect('sprin:detail', pk=pk)

    return render(request, 'sprin/form_sprin.html', {'sprin': sprin, 'action': 'edit'})


# ─── Ajukan Sprin ke Menunggu Paraf ─────────────────────────────────────────
@login_required
def ajukan_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    if not _can_manage_sprin(request.user):
        messages.error(request, 'Akses ditolak.')
        return redirect('sprin:detail', pk=pk)
    if not sprin.dapat_diajukan:
        messages.error(request, 'Sprin ini tidak dapat diajukan.')
        return redirect('sprin:detail', pk=pk)
    sprin.status = 'menunggu_paraf'
    sprin.save()
    messages.success(request, f'Sprin {sprin.nomor} berhasil diajukan untuk paraf.')
    return redirect('sprin:detail', pk=pk)


# ─── PBI-023: Cancel Sprin (Operator) ────────────────────────────────────────
@login_required
def batal_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    if not _can_manage_sprin(request.user):
        messages.error(request, 'Hanya Operator atau Admin yang dapat membatalkan Sprin.')
        return redirect('sprin:detail', pk=pk)

    if not sprin.dapat_dibatalkan:
        messages.error(request, f'Sprin dengan status "{sprin.get_status_display()}" tidak dapat dibatalkan.')
        return redirect('sprin:detail', pk=pk)

    if request.method == 'POST':
        alasan = request.POST.get('alasan', '').strip()
        sprin.status = 'dibatalkan'
        sprin.alasan_batal = alasan
        sprin.dibatalkan_oleh = request.user
        sprin.dibatalkan_pada = timezone.now()
        sprin.save()
        messages.success(request, f'Sprin {sprin.nomor} berhasil dibatalkan.')
        return redirect('sprin:detail', pk=pk)

    return render(request, 'sprin/konfirmasi_batal.html', {'sprin': sprin})


# ─── PBI-028: Approve/Reject Sprin (Pimpinan) ────────────────────────────────
@login_required
def aksi_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    if not _can_approve_sprin(request.user):
        messages.error(request, 'Hanya Pimpinan yang dapat menyetujui/menolak Sprin.')
        return redirect('sprin:detail', pk=pk)

    if not sprin.dapat_disetujui:
        messages.error(request, 'Sprin ini tidak memenuhi syarat untuk disetujui/ditolak.')
        return redirect('sprin:detail', pk=pk)

    aksi = request.GET.get('aksi', request.POST.get('aksi', ''))

    if request.method == 'POST':
        catatan = request.POST.get('catatan', '').strip()
        if aksi == 'setujui':
            sprin.status = 'disetujui'
            sprin.catatan_pimpinan = catatan
            sprin.disetujui_oleh = request.user
            sprin.disetujui_pada = timezone.now()
            sprin.save()
            messages.success(request, f'Sprin {sprin.nomor} telah disetujui.')
        elif aksi == 'tolak':
            if not catatan:
                messages.error(request, 'Catatan/alasan penolakan wajib diisi.')
                return render(request, 'sprin/konfirmasi_aksi.html', {'sprin': sprin, 'aksi': aksi})
            sprin.status = 'ditolak'
            sprin.catatan_pimpinan = catatan
            sprin.disetujui_oleh = request.user
            sprin.disetujui_pada = timezone.now()
            sprin.save()
            messages.success(request, f'Sprin {sprin.nomor} telah ditolak.')
        return redirect('sprin:detail', pk=pk)

    return render(request, 'sprin/konfirmasi_aksi.html', {'sprin': sprin, 'aksi': aksi})


# ─── Tambah Personel ke Sprin ────────────────────────────────────────────────
@login_required
def tambah_personel_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    if not _can_manage_sprin(request.user):
        messages.error(request, 'Akses ditolak.')
        return redirect('sprin:detail', pk=pk)
    if request.method == 'POST':
        personel_ids = request.POST.getlist('personel_ids')
        jabatan = request.POST.get('jabatan_dalam_sprin', '')
        for idx, pid in enumerate(personel_ids, 1):
            PersonelSprin.objects.get_or_create(
                sprin=sprin,
                personel_id=pid,
                defaults={'nomor_urut': sprin.personel_list.count() + idx, 'jabatan_dalam_sprin': jabatan},
            )
        messages.success(request, f'{len(personel_ids)} personel berhasil ditambahkan.')
    return redirect('sprin:detail', pk=pk)


# ─── Hapus Sprin (hanya draft) ───────────────────────────────────────────────
@login_required
def hapus_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    if not _can_manage_sprin(request.user):
        messages.error(request, 'Akses ditolak.')
        return redirect('sprin:detail', pk=pk)
    if sprin.status != 'draft':
        messages.error(request, 'Hanya Sprin draft yang bisa dihapus.')
        return redirect('sprin:detail', pk=pk)
    if request.method == 'POST':
        nomor = sprin.nomor
        sprin.delete()
        messages.success(request, f'Sprin {nomor} berhasil dihapus.')
        return redirect('sprin:daftar')
    return render(request, 'sprin/konfirmasi_hapus.html', {'sprin': sprin})
