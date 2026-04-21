from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Personel, Satker, Role
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone

def redirect_root(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('accounts:login')

# Autentikasi
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

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        nrp = request.POST.get('nrp', '').strip()
        nama = request.POST.get('nama_lengkap', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        satker_id = request.POST.get('satker')
        pangkat = request.POST.get('pangkat', '')

        if not nrp or not nama:
            messages.error(request, 'NRP dan Nama Lengkap wajib diisi.')
        elif Personel.objects.filter(nrp=nrp).exists():
            messages.error(request, 'NRP sudah terdaftar di sistem.')
        elif password1 != password2:
            messages.error(request, 'Konfirmasi password tidak cocok.')
        elif len(password1) < 8:
            messages.error(request, 'Password minimal 8 karakter.')
        else:
            satker = Satker.objects.filter(pk=satker_id).first() if satker_id else None
            user = Personel.objects.create_user(
                nrp=nrp,
                password=password1,
                nama_lengkap=nama,
                pangkat=pangkat,
                satker=satker,
            )
            login(request, user)
            messages.success(request, f'Selamat datang, {user.nama_lengkap}!')
            return redirect('dashboard:index')

    satker_list = Satker.objects.all()
    pangkat_choices = Personel.PANGKAT_CHOICES
    return render(request, 'accounts/register.html', {
        'satker_list': satker_list,
        'pangkat_choices': pangkat_choices,
    })

# Manajemen Personel
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
    role_filter = request.GET.get('role', '').strip()
    satker_filter = request.GET.get('satker', '').strip()
    status_filter = request.GET.get('status', '').strip()

    personel_list = Personel.objects.select_related('satker').order_by('nama_lengkap')

    if q:
        personel_list = personel_list.filter(Q(nama_lengkap__icontains=q) | Q(nrp__icontains=q))
    if role_filter:
        personel_list = personel_list.filter(role_obj_id=role_filter) # Gunakan ID role
    if satker_filter:
        personel_list = personel_list.filter(satker_id=satker_filter)
    if status_filter == 'aktif':
        personel_list = personel_list.filter(is_active=True)
    elif status_filter == 'nonaktif':
        personel_list = personel_list.filter(is_active=False)

    paginator = Paginator(personel_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    role_list = Role.objects.all()
    satker_list = Satker.objects.all()

    base_queryset = Personel.objects.all()
    total_keseluruhan = base_queryset.count()
    total_aktif = base_queryset.filter(is_active=True).count()
    total_nonaktif = base_queryset.filter(is_active=False).count()

    return render(request, 'accounts/daftar_personel.html', {
        'page_obj': page_obj,
        'total_data_filter': paginator.count,
        'total_keseluruhan': total_keseluruhan,
        'total_aktif': total_aktif,
        'total_nonaktif': total_nonaktif,
        'q': q,
        'role_list': role_list,
        'satker_list': satker_list,
    })

@login_required
def tambah_personel_view(request):
    if not request.user.is_superadmin:
        messages.error(request, 'Akses ditolak.')
        return redirect('accounts:daftar_personel')

    if request.method == 'POST':
        nrp = request.POST.get('nrp', '').strip()
        nama = request.POST.get('nama_lengkap', '').strip()
        email = request.POST.get('email', '').strip()
        pangkat = request.POST.get('pangkat', '')
        jabatan = request.POST.get('jabatan', '').strip()
        role_id = request.POST.get('role')
        satker_id = request.POST.get('satker')
        no_hp = request.POST.get('no_hp', '').strip()
        password = request.POST.get('password', '')

        if not nrp.isdigit() or len(nrp) != 8:
            messages.error(request, 'NRP harus berupa 8 digit angka.')
        elif Personel.objects.filter(nrp=nrp).exists():
            messages.error(request, 'NRP sudah terdaftar.')
        elif len(password) < 8:
            messages.error(request, 'Password minimal 8 karakter.')
        else:
            satker = Satker.objects.filter(pk=satker_id).first()
            role_obj = Role.objects.filter(pk=role_id).first()
            
            Personel.objects.create_user(
                nrp=nrp, password=password, nama_lengkap=nama,
                email=email, pangkat=pangkat, jabatan=jabatan,
                role_obj=role_obj, satker=satker, no_hp=no_hp
            )
            messages.success(request, f'Personel {nama} berhasil ditambahkan.')
            return redirect('accounts:daftar_personel')

    satker_list = Satker.objects.all()
    role_list = Role.objects.all()
    return render(request, 'accounts/form_personel.html', {
        'satker_list': satker_list,
        'role_list': role_list,
        'pangkat_choices': Personel.PANGKAT_CHOICES,
        'action': 'tambah',
        'form_data': request.POST if request.method == 'POST' else {}
    })

@login_required
def edit_personel_view(request, pk):
    if not request.user.is_superadmin:
        messages.error(request, 'Akses ditolak.')
        return redirect('accounts:daftar_personel')

    personel = get_object_or_404(Personel, pk=pk)
    
    if request.method == 'POST':
        personel.nama_lengkap = request.POST.get('nama_lengkap', '').strip()
        personel.email = request.POST.get('email', '').strip()
        personel.pangkat = request.POST.get('pangkat', '')
        personel.jabatan = request.POST.get('jabatan', '').strip()
        personel.no_hp = request.POST.get('no_hp', '').strip()
        
        satker_id = request.POST.get('satker')
        role_id = request.POST.get('role')
        personel.satker = Satker.objects.filter(pk=satker_id).first()
        if role_id:
            personel.role_obj = Role.objects.filter(pk=role_id).first()
        
        new_password = request.POST.get('password', '').strip()
        if new_password:
            if len(new_password) < 8:
                messages.error(request, 'Password baru minimal 8 karakter.')
                return render(request, 'accounts/form_personel.html', {
                    'personel': personel, 'action': 'edit', 
                    'satker_list': Satker.objects.all(), 'role_list': Role.objects.all()
                })
            personel.set_password(new_password)
            
        personel.save()
        messages.success(request, f'Data {personel.nama_lengkap} berhasil diperbarui.')
        return redirect('accounts:daftar_personel')

    return render(request, 'accounts/form_personel.html', {
        'personel': personel,
        'satker_list': Satker.objects.all(),
        'role_list': Role.objects.all(),
        'pangkat_choices': Personel.PANGKAT_CHOICES,
        'action': 'edit',
    })

@login_required
def hapus_personel_view(request, pk):
    if not request.user.is_superadmin:
        messages.error(request, 'Akses ditolak.')
        return redirect('accounts:daftar_personel')

    personel = get_object_or_404(Personel, pk=pk)
    
    if request.method == 'POST':
        # Ambil alasan dari form (kita akan buat inputnya di template konfirmasi)
        alasan = request.POST.get('alasan', 'Tidak ada alasan spesifik')
        
        personel.is_active = False
        personel.tanggal_nonaktif = timezone.now()
        personel.alasan_nonaktif = alasan
        personel.save()
        
        messages.success(request, f'Akun {personel.nama_lengkap} telah dinonaktifkan.')
        return redirect('accounts:detail_personel', pk=personel.pk)

    return render(request, 'accounts/konfirmasi_hapus.html', {'personel': personel})

@login_required
def detail_personel_view(request, pk):
    if request.user.role not in ('superadmin', 'operator') and request.user.pk != pk:
        messages.error(request, 'Anda tidak memiliki akses untuk melihat profil ini.')
        return redirect('dashboard:index')

    personel = get_object_or_404(Personel, pk=pk)
    
    return render(request, 'accounts/detail_personel.html', {
        'personel': personel,
    })

@login_required
def reaktivasi_personel_view(request, pk):
    if request.user.role != 'superadmin' and not request.user.is_superadmin:
        messages.error(request, 'Hanya Superadmin yang dapat mereaktivasi personel.')
        return redirect('accounts:daftar_personel')

    personel = get_object_or_404(Personel, pk=pk)
    if request.method == 'POST':
        nama = personel.nama_lengkap
        personel.is_active = True # REAKTIVASI
        personel.save()
        messages.success(request, f'Personel {nama} berhasil direaktivasi.')
        return redirect('accounts:daftar_personel')

    return render(request, 'accounts/konfirmasi_reaktivasi.html', {'personel': personel})

# Manajemen Role 
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
