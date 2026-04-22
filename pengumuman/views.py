from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.cache import never_cache
from .models import Pengumuman
from .forms import PengumumanForm

def is_admin_or_pimpinan(user):
    return getattr(user, 'role', '') in ['superadmin', 'operator', 'pimpinan']

@never_cache
@login_required
def daftar_pengumuman(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    
    if is_admin_or_pimpinan(request.user):
        # Admin/Pimpinan sees all announcements
        pengumuman_list = Pengumuman.objects.prefetch_related('dibaca_oleh').all()
    else:
        # Normal user only sees active announcements that are within the display period
        now = timezone.now()
        pengumuman_list = Pengumuman.objects.prefetch_related('dibaca_oleh').filter(is_active=True).filter(
            Q(periode_mulai__isnull=True) | Q(periode_mulai__lte=now)
        ).filter(
            Q(periode_selesai__isnull=True) | Q(periode_selesai__gte=now)
        )

    if q:
        pengumuman_list = pengumuman_list.filter(
            Q(judul__icontains=q) | Q(isi__icontains=q)
        )

    if status == 'aktif':
        pengumuman_list = pengumuman_list.filter(is_active=True)
    elif status == 'nonaktif':
        pengumuman_list = pengumuman_list.filter(is_active=False)

    return render(request, 'pengumuman/daftar_pengumuman.html', {
        'pengumuman_list': pengumuman_list,
        'q': q,
        'selected_status': status,
        'is_admin': is_admin_or_pimpinan(request.user),
        'active_nav': 'pengumuman'
    })

@login_required
def detail_pengumuman(request, pk):
    pengumuman = get_object_or_404(Pengumuman, pk=pk)
    
    # Restrict normal users from viewing inactive announcements
    if not is_admin_or_pimpinan(request.user) and pengumuman.status_tayang != "Sedang Tayang":
        messages.error(request, 'Pengumuman tidak dapat diakses saat ini.')
        return redirect('pengumuman:daftar')

    # Mark as read
    pengumuman.dibaca_oleh.add(request.user)

    return render(request, 'pengumuman/detail_pengumuman.html', {
        'pengumuman': pengumuman,
        'is_admin': is_admin_or_pimpinan(request.user),
        'active_nav': 'pengumuman'
    })

@login_required
def tambah_pengumuman(request):
    if not is_admin_or_pimpinan(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk menambah pengumuman.')
        return redirect('pengumuman:daftar')

    if request.method == 'POST':
        form = PengumumanForm(request.POST)
        if form.is_valid():
            pengumuman = form.save(commit=False)
            pengumuman.dibuat_oleh = request.user
            pengumuman.save()
            messages.success(request, 'Pengumuman berhasil ditambahkan.')
            return redirect('pengumuman:daftar')
    else:
        form = PengumumanForm()

    return render(request, 'pengumuman/form_pengumuman.html', {
        'form': form,
        'title': 'Tambah Pengumuman',
        'is_admin': True,
        'active_nav': 'pengumuman'
    })

@login_required
def edit_pengumuman(request, pk):
    if not is_admin_or_pimpinan(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengubah pengumuman.')
        return redirect('pengumuman:daftar')

    pengumuman = get_object_or_404(Pengumuman, pk=pk)
    
    if request.method == 'POST':
        form = PengumumanForm(request.POST, instance=pengumuman)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pengumuman berhasil diubah.')
            return redirect('pengumuman:detail', pk=pengumuman.pk)
    else:
        form = PengumumanForm(instance=pengumuman)

    return render(request, 'pengumuman/form_pengumuman.html', {
        'form': form,
        'title': 'Edit Pengumuman',
        'pengumuman': pengumuman,
        'is_admin': True,
        'active_nav': 'pengumuman'
    })

@login_required
def hapus_pengumuman(request, pk):
    if not is_admin_or_pimpinan(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk menghapus pengumuman.')
        return redirect('pengumuman:daftar')

    pengumuman = get_object_or_404(Pengumuman, pk=pk)
    
    if request.method == 'POST':
        judul = pengumuman.judul
        pengumuman.delete()
        messages.success(request, f'Pengumuman "{judul}" berhasil dihapus.')
        return redirect('pengumuman:daftar')

    return render(request, 'pengumuman/konfirmasi_hapus_pengumuman.html', {
        'pengumuman': pengumuman,
        'is_admin': True,
        'active_nav': 'pengumuman'
    })

@login_required
def toggle_status_pengumuman(request, pk):
    if not is_admin_or_pimpinan(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengubah status pengumuman.')
        return redirect('pengumuman:daftar')

    pengumuman = get_object_or_404(Pengumuman, pk=pk)
    if request.method == 'POST':
        pengumuman.is_active = not pengumuman.is_active
        pengumuman.save()
        status_text = "diaktifkan" if pengumuman.is_active else "dinonaktifkan"
        messages.success(request, f'Status pengumuman berhasil {status_text}.')
        
    return redirect('pengumuman:detail', pk=pk)

@login_required
def tandai_semua_dibaca(request):
    now = timezone.now()
    active_pengumuman = Pengumuman.objects.filter(is_active=True).filter(
        Q(periode_mulai__isnull=True) | Q(periode_mulai__lte=now)
    ).filter(
        Q(periode_selesai__isnull=True) | Q(periode_selesai__gte=now)
    )
    
    for p in active_pengumuman:
        p.dibaca_oleh.add(request.user)
        
    messages.success(request, 'Semua pengumuman telah ditandai sebagai dibaca.')
    return redirect('pengumuman:daftar')
