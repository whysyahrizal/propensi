from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import PengajuanCuti
from notifikasi.models import Notifikasi


@login_required
def daftar_cuti(request):
    role = request.user.role
    if role == 'personel':
        cuti_list = PengajuanCuti.objects.filter(personel=request.user)
    elif role in ('pimpinan',):
        cuti_list = PengajuanCuti.objects.filter(
            personel__satker=request.user.satker
        ).exclude(personel=request.user)
    else:
        cuti_list = PengajuanCuti.objects.all().select_related('personel', 'disetujui_oleh')
    return render(request, 'cuti/daftar_cuti.html', {'cuti_list': cuti_list})


@login_required
def ajukan_cuti(request):
    if request.method == 'POST':
        cuti = PengajuanCuti(
            personel=request.user,
            jenis_cuti=request.POST['jenis_cuti'],
            tanggal_mulai=request.POST['tanggal_mulai'],
            tanggal_selesai=request.POST['tanggal_selesai'],
            alasan=request.POST['alasan'],
        )
        if 'dokumen_pendukung' in request.FILES:
            cuti.dokumen_pendukung = request.FILES['dokumen_pendukung']
        cuti.save()
        messages.success(request, 'Pengajuan cuti berhasil diajukan dan menunggu persetujuan.')
        return redirect('cuti:daftar')

    return render(request, 'cuti/form_cuti.html', {
        'jenis_choices': PengajuanCuti.JENIS_CUTI_CHOICES,
    })


@login_required
def detail_cuti(request, pk):
    cuti = get_object_or_404(PengajuanCuti, pk=pk)
    return render(request, 'cuti/detail_cuti.html', {'cuti': cuti})


@login_required
def setujui_cuti(request, pk):
    if request.user.role not in ('pimpinan', 'superadmin'):
        messages.error(request, 'Anda tidak berwenang menyetujui cuti.')
        return redirect('cuti:daftar')
    cuti = get_object_or_404(PengajuanCuti, pk=pk, status='menunggu')
    if request.method == 'POST':
        cuti.status = 'disetujui'
        cuti.catatan_pimpinan = request.POST.get('catatan', '')
        cuti.disetujui_oleh = request.user
        cuti.diproses_pada = timezone.now()
        cuti.save()
        Notifikasi.objects.create(
            penerima=cuti.personel,
            judul='Cuti Disetujui',
            pesan=f'Pengajuan {cuti.get_jenis_cuti_display()} Anda telah disetujui.',
            tipe='cuti_status',
            url_ref=f'/cuti/{cuti.pk}/',
        )
        messages.success(request, 'Pengajuan cuti berhasil disetujui.')
        return redirect('cuti:daftar')
    return render(request, 'cuti/konfirmasi_aksi.html', {'cuti': cuti, 'aksi': 'setujui'})


@login_required
def tolak_cuti(request, pk):
    if request.user.role not in ('pimpinan', 'superadmin'):
        messages.error(request, 'Anda tidak berwenang menolak cuti.')
        return redirect('cuti:daftar')
    cuti = get_object_or_404(PengajuanCuti, pk=pk, status='menunggu')
    if request.method == 'POST':
        cuti.status = 'ditolak'
        cuti.catatan_pimpinan = request.POST.get('catatan', '')
        cuti.disetujui_oleh = request.user
        cuti.diproses_pada = timezone.now()
        cuti.save()
        Notifikasi.objects.create(
            penerima=cuti.personel,
            judul='Cuti Ditolak',
            pesan=f'Pengajuan {cuti.get_jenis_cuti_display()} Anda ditolak. Catatan: {cuti.catatan_pimpinan}',
            tipe='cuti_status',
            url_ref=f'/cuti/{cuti.pk}/',
        )
        messages.success(request, 'Pengajuan cuti berhasil ditolak.')
        return redirect('cuti:daftar')
    return render(request, 'cuti/konfirmasi_aksi.html', {'cuti': cuti, 'aksi': 'tolak'})


@login_required
def upload_surat_cuti(request, pk):
    if request.user.role != 'superadmin':
        messages.error(request, 'Hanya Superadmin yang dapat mengunggah surat resmi.')
        return redirect('cuti:daftar')
    cuti = get_object_or_404(PengajuanCuti, pk=pk, status='disetujui')
    if request.method == 'POST' and 'file_surat_resmi' in request.FILES:
        cuti.file_surat_resmi = request.FILES['file_surat_resmi']
        cuti.save()
        Notifikasi.objects.create(
            penerima=cuti.personel,
            judul='Surat Cuti Resmi Tersedia',
            pesan='Surat cuti resmi Anda telah diterbitkan dan dapat diunduh.',
            tipe='surat_diterbitkan',
            url_ref=f'/cuti/{cuti.pk}/',
        )
        messages.success(request, 'Surat resmi berhasil diunggah.')
    return redirect('cuti:detail', pk=pk)


@login_required
def monitoring_cuti(request):
    if request.user.role not in ('superadmin', 'operator'):
        messages.error(request, 'Akses ditolak.')
        return redirect('cuti:daftar')
    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '')
    cuti_list = PengajuanCuti.objects.select_related('personel', 'disetujui_oleh').order_by('-diajukan_pada')
    if status_filter:
        cuti_list = cuti_list.filter(status=status_filter)
    if q:
        cuti_list = cuti_list.filter(
            personel__nama_lengkap__icontains=q
        ) | cuti_list.filter(personel__nrp__icontains=q)
    return render(request, 'cuti/monitoring.html', {
        'cuti_list': cuti_list,
        'status_choices': PengajuanCuti.STATUS_CHOICES,
        'status_filter': status_filter,
        'q': q,
    })
