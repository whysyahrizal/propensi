from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pengumuman


@login_required
def daftar_pengumuman(request):
    role = request.user.role
    if role in ('superadmin', 'pimpinan'):
        pengumuman_list = Pengumuman.objects.all()
    else:
        pengumuman_list = Pengumuman.objects.filter(is_published=True)
    return render(request, 'pengumuman/daftar.html', {'pengumuman_list': pengumuman_list})


@login_required
def detail_pengumuman(request, pk):
    pengumuman = get_object_or_404(Pengumuman, pk=pk)
    return render(request, 'pengumuman/detail.html', {'pengumuman': pengumuman})


@login_required
def tambah_pengumuman(request):
    if request.user.role not in ('superadmin', 'pimpinan'):
        messages.error(request, 'Anda tidak berwenang membuat pengumuman.')
        return redirect('pengumuman:daftar')
    if request.method == 'POST':
        p = Pengumuman(
            judul=request.POST['judul'],
            konten=request.POST['konten'],
            dibuat_oleh=request.user,
            is_published=request.POST.get('is_published', 'off') == 'on',
        )
        if 'lampiran' in request.FILES:
            p.lampiran = request.FILES['lampiran']
        p.save()
        messages.success(request, 'Pengumuman berhasil diterbitkan.')
        return redirect('pengumuman:daftar')
    return render(request, 'pengumuman/form.html', {'action': 'tambah'})


@login_required
def edit_pengumuman(request, pk):
    if request.user.role not in ('superadmin', 'pimpinan'):
        messages.error(request, 'Anda tidak berwenang mengedit pengumuman.')
        return redirect('pengumuman:daftar')
    p = get_object_or_404(Pengumuman, pk=pk)
    if request.method == 'POST':
        p.judul = request.POST.get('judul', p.judul)
        p.konten = request.POST.get('konten', p.konten)
        p.is_published = request.POST.get('is_published', 'off') == 'on'
        if 'lampiran' in request.FILES:
            p.lampiran = request.FILES['lampiran']
        p.save()
        messages.success(request, 'Pengumuman berhasil diperbarui.')
        return redirect('pengumuman:detail', pk=pk)
    return render(request, 'pengumuman/form.html', {'pengumuman': p, 'action': 'edit'})


@login_required
def hapus_pengumuman(request, pk):
    if request.user.role not in ('superadmin', 'pimpinan'):
        messages.error(request, 'Anda tidak berwenang menghapus pengumuman.')
        return redirect('pengumuman:daftar')
    p = get_object_or_404(Pengumuman, pk=pk)
    if request.method == 'POST':
        p.delete()
        messages.success(request, 'Pengumuman berhasil dihapus.')
        return redirect('pengumuman:daftar')
    return render(request, 'pengumuman/konfirmasi_hapus.html', {'pengumuman': p})
