from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Personel, Satker, Role


def redirect_root(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('accounts:login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        nrp = request.POST.get('nrp', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=nrp, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        else:
            messages.error(request, 'NRP atau password salah. Silakan coba lagi.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Anda berhasil keluar dari sistem.')
    return redirect('accounts:login')



@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.nama_lengkap = request.POST.get('nama_lengkap', user.nama_lengkap)
        user.email = request.POST.get('email', user.email)
        user.no_hp = request.POST.get('no_hp', user.no_hp)
        user.jabatan = request.POST.get('jabatan', user.jabatan)
        if 'foto' in request.FILES:
            user.foto = request.FILES['foto']
        user.save()
        messages.success(request, 'Profil berhasil diperbarui.')
        return redirect('accounts:profil')

    return render(request, 'accounts/profil.html', {'user': request.user})


@login_required
def daftar_personel_view(request):
    if request.user.role not in ('superadmin', 'operator'):
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('dashboard:index')

    q = request.GET.get('q', '').strip()
    personel_list = Personel.objects.select_related('satker').order_by('nama_lengkap')
    if q:
        personel_list = personel_list.filter(
            nama_lengkap__icontains=q
        ) | personel_list.filter(nrp__icontains=q)

    return render(request, 'accounts/daftar_personel.html', {
        'personel_list': personel_list,
        'q': q,
    })


@login_required
def tambah_personel_view(request):
    if request.user.role != 'superadmin':
        messages.error(request, 'Hanya Superadmin yang dapat menambah personel.')
        return redirect('accounts:daftar_personel')

    if request.method == 'POST':
        nrp = request.POST.get('nrp', '').strip()
        nama = request.POST.get('nama_lengkap', '').strip()
        pangkat = request.POST.get('pangkat', '')
        jabatan = request.POST.get('jabatan', '')
        role = request.POST.get('role', 'personel')
        satker_id = request.POST.get('satker')
        email = request.POST.get('email', '')
        no_hp = request.POST.get('no_hp', '')

        if Personel.objects.filter(nrp=nrp).exists():
            messages.error(request, 'NRP sudah terdaftar.')
        else:
            satker = Satker.objects.filter(pk=satker_id).first() if satker_id else None
            Personel.objects.create_user(
                nrp=nrp, password='siraga2026',  # default password, wajib diganti
                nama_lengkap=nama, pangkat=pangkat, jabatan=jabatan,
                role=role, satker=satker, email=email, no_hp=no_hp,
            )
            messages.success(request, f'Personel {nama} berhasil ditambahkan. Password default: siraga2026')
            return redirect('accounts:daftar_personel')

    satker_list = Satker.objects.all()
    return render(request, 'accounts/form_personel.html', {
        'satker_list': satker_list,
        'pangkat_choices': Personel.PANGKAT_CHOICES,
        'role_choices': Personel.ROLE_CHOICES,
        'action': 'tambah',
    })


@login_required
def edit_personel_view(request, pk):
    if request.user.role != 'superadmin':
        messages.error(request, 'Hanya Superadmin yang dapat mengedit personel.')
        return redirect('accounts:daftar_personel')

    personel = get_object_or_404(Personel, pk=pk)
    if request.method == 'POST':
        personel.nama_lengkap = request.POST.get('nama_lengkap', personel.nama_lengkap)
        personel.pangkat = request.POST.get('pangkat', personel.pangkat)
        personel.jabatan = request.POST.get('jabatan', personel.jabatan)
        personel.role = request.POST.get('role', personel.role)
        personel.email = request.POST.get('email', personel.email)
        personel.no_hp = request.POST.get('no_hp', personel.no_hp)
        satker_id = request.POST.get('satker')
        personel.satker = Satker.objects.filter(pk=satker_id).first() if satker_id else None
        personel.save()
        messages.success(request, 'Data personel berhasil diperbarui.')
        return redirect('accounts:daftar_personel')

    satker_list = Satker.objects.all()
    return render(request, 'accounts/form_personel.html', {
        'personel': personel,
        'satker_list': satker_list,
        'pangkat_choices': Personel.PANGKAT_CHOICES,
        'role_choices': Personel.ROLE_CHOICES,
        'action': 'edit',
    })


@login_required
def hapus_personel_view(request, pk):
    if request.user.role != 'superadmin':
        messages.error(request, 'Hanya Superadmin yang dapat menghapus personel.')
        return redirect('accounts:daftar_personel')

    personel = get_object_or_404(Personel, pk=pk)
    if request.method == 'POST':
        nama = personel.nama_lengkap
        personel.delete()
        messages.success(request, f'Personel {nama} berhasil dihapus.')
        return redirect('accounts:daftar_personel')

    return render(request, 'accounts/konfirmasi_hapus.html', {'personel': personel})


# ─── EPIC03 — Manajemen Role (PBI-011 to PBI-015) ────────────────────────────

def _superadmin_required(request):
    """Cek apakah user adalah superadmin; kembalikan True jika boleh akses."""
    return request.user.is_authenticated and request.user.role == 'superadmin'


@login_required
def daftar_role(request):
    """PBI-011 — Tampilkan daftar semua role dengan pagination & search."""
    if not _superadmin_required(request):
        messages.error(request, 'Akses ditolak. Hanya Superadmin yang dapat mengelola role.')
        return redirect('dashboard:index')

    q = request.GET.get('q', '').strip()
    role_list = Role.objects.all()
    if q:
        role_list = role_list.filter(nama__icontains=q)

    # Pagination manual (10 per halaman)
    from django.core.paginator import Paginator
    paginator = Paginator(role_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/role/daftar_role.html', {
        'page_obj': page_obj,
        'total': role_list.count(),
        'q': q,
    })


@login_required
def detail_role(request, pk):
    """PBI-012 — Tampilkan detail role; 404 jika tidak ditemukan."""
    if not _superadmin_required(request):
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard:index')

    role = get_object_or_404(Role, pk=pk)
    pengguna_list = role.personel_set.filter(is_active=True).select_related('satker')
    return render(request, 'accounts/role/detail_role.html', {
        'role': role,
        'pengguna_list': pengguna_list,
    })


@login_required
def tambah_role(request):
    """PBI-013 — Tambah role baru; validasi nama tidak kosong & unik."""
    if not _superadmin_required(request):
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        deskripsi = request.POST.get('deskripsi', '').strip()

        if not nama:
            messages.error(request, 'Nama role tidak boleh kosong.')
        elif Role.objects.filter(nama__iexact=nama).exists():
            messages.error(request, f'Role dengan nama "{nama}" sudah ada.')
        else:
            role = Role.objects.create(nama=nama, deskripsi=deskripsi)
            messages.success(request, f'Role "{role.nama}" berhasil ditambahkan.')
            return redirect('accounts:daftar_role')

    return render(request, 'accounts/role/form_role.html', {
        'action': 'tambah',
        'form_data': request.POST if request.method == 'POST' else {},
    })


@login_required
def edit_role(request, pk):
    """PBI-014 — Edit nama/deskripsi role; validasi nama tetap unik."""
    if not _superadmin_required(request):
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard:index')

    role = get_object_or_404(Role, pk=pk)

    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        deskripsi = request.POST.get('deskripsi', '').strip()

        if not nama:
            messages.error(request, 'Nama role tidak boleh kosong.')
        elif Role.objects.filter(nama__iexact=nama).exclude(pk=pk).exists():
            messages.error(request, f'Role dengan nama "{nama}" sudah digunakan.')
        else:
            role.nama = nama
            role.deskripsi = deskripsi
            role.save()
            messages.success(request, f'Role "{role.nama}" berhasil diperbarui.')
            return redirect('accounts:detail_role', pk=role.pk)

    return render(request, 'accounts/role/form_role.html', {
        'action': 'edit',
        'role': role,
        'form_data': request.POST if request.method == 'POST' else {},
    })


@login_required
def hapus_role(request, pk):
    """PBI-015 — Hapus role; tolak jika masih dipakai pengguna aktif."""
    if not _superadmin_required(request):
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard:index')

    role = get_object_or_404(Role, pk=pk)
    jumlah_pengguna = role.personel_set.filter(is_active=True).count()

    if request.method == 'POST':
        if jumlah_pengguna > 0:
            messages.error(
                request,
                f'Role "{role.nama}" tidak dapat dihapus karena masih digunakan oleh '
                f'{jumlah_pengguna} pengguna aktif.'
            )
            return redirect('accounts:detail_role', pk=role.pk)
        nama = role.nama
        role.delete()
        messages.success(request, f'Role "{nama}" berhasil dihapus.')
        return redirect('accounts:daftar_role')

    return render(request, 'accounts/role/konfirmasi_hapus_role.html', {
        'role': role,
        'jumlah_pengguna': jumlah_pengguna,
    })
