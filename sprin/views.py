from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sprin, PersonelSprin
from accounts.models import Personel


@login_required
def daftar_sprin(request):
    role = request.user.role
    if role == 'personel':
        # Personel hanya lihat sprin aktif miliknya
        sprin_list = Sprin.objects.filter(
            personel_list__personel=request.user
        ).distinct().order_by('-tanggal')
    else:
        sprin_list = Sprin.objects.all().select_related('dibuat_oleh')
    return render(request, 'sprin/daftar_sprin.html', {'sprin_list': sprin_list})


@login_required
def detail_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    personel_sprin = sprin.personel_list.select_related('personel').all()
    return render(request, 'sprin/detail_sprin.html', {
        'sprin': sprin,
        'personel_sprin': personel_sprin,
    })


@login_required
def tambah_sprin(request):
    if request.user.role not in ('operator', 'pimpinan', 'superadmin'):
        messages.error(request, 'Anda tidak memiliki akses.')
        return redirect('sprin:daftar')

    if request.method == 'POST':
        sprin = Sprin.objects.create(
            nomor=request.POST['nomor'],
            tanggal=request.POST['tanggal'],
            perihal=request.POST['perihal'],
            dasar=request.POST.get('dasar', ''),
            isi_perintah=request.POST.get('isi_perintah', ''),
            dibuat_oleh=request.user,
            status='draft',
        )
        messages.success(request, f'Sprin {sprin.nomor} berhasil dibuat.')
        return redirect('sprin:detail', pk=sprin.pk)

    return render(request, 'sprin/form_sprin.html', {'action': 'tambah'})


@login_required
def edit_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    if sprin.status != 'draft':
        messages.error(request, 'Sprin yang sudah diajukan tidak dapat diedit.')
        return redirect('sprin:detail', pk=pk)

    if request.method == 'POST':
        sprin.nomor = request.POST.get('nomor', sprin.nomor)
        sprin.tanggal = request.POST.get('tanggal', sprin.tanggal)
        sprin.perihal = request.POST.get('perihal', sprin.perihal)
        sprin.dasar = request.POST.get('dasar', sprin.dasar)
        sprin.isi_perintah = request.POST.get('isi_perintah', sprin.isi_perintah)
        sprin.save()
        messages.success(request, 'Sprin berhasil diperbarui.')
        return redirect('sprin:detail', pk=pk)

    return render(request, 'sprin/form_sprin.html', {'sprin': sprin, 'action': 'edit'})


@login_required
def hapus_sprin(request, pk):
    sprin = get_object_or_404(Sprin, pk=pk)
    if sprin.status != 'draft':
        messages.error(request, 'Hanya Sprin draft yang bisa dihapus.')
        return redirect('sprin:detail', pk=pk)
    if request.method == 'POST':
        nomor = sprin.nomor
        sprin.delete()
        messages.success(request, f'Sprin {nomor} berhasil dihapus.')
        return redirect('sprin:daftar')
    return render(request, 'sprin/konfirmasi_hapus.html', {'sprin': sprin})
