"""
Management command: seed_data
Mengisi database dengan data dummy untuk keperluan testing.

Jalankan dengan:
    python manage.py seed_data
    python manage.py seed_data --reset   # hapus data sebelumnya dulu
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import MenuItem, Personel, Satker, Role
from locations.models import Location
from schedules.models import ShiftSchedule  # Ditambah untuk mengelakkan ProtectedError

SATKER_DATA = [
    {"kode": "DITLANTAS",  "nama": "Direktorat Lalu Lintas"},
    {"kode": "DITGAKKUM",  "nama": "Direktorat Penegakan Hukum"},
    {"kode": "SUBDITREGID","nama": "Subdirektorat Registrasi & Identifikasi"},
    {"kode": "SUBDITKAMSEL","nama": "Subdirektorat Keamanan & Keselamatan"},
    {"kode": "BAGOPS",     "nama": "Bagian Operasional"},
    {"kode": "BAGRENMIN",  "nama": "Bagian Perencanaan & Administrasi"},
    {"kode": "NTMC",       "nama": "National Traffic Management Centre"},
]

ROLE_DATA = [
    {"nama": "superadmin", "display_label": "Superadmin", "deskripsi": "Akses penuh ke seluruh sistem dan pengaturan."},
    {"nama": "pimpinan", "display_label": "Pimpinan", "deskripsi": "Akses pemantauan dashboard dan persetujuan."},
    {"nama": "operator", "display_label": "Operator", "deskripsi": "Akses kelola data personel dan absensi harian."},
    {"nama": "personel", "display_label": "Personel", "deskripsi": "Akses dasar pengguna untuk absen dan riwayat."},
]

MENU_HIERARCHY = [
    # MENU UTAMA
    {
        "key": "dashboard", "label": "Dashboard", "path": "dashboard:index", "icon": "heroicons:home", "sort_order": 1,
        "children": []
    },

    # GRUP: KEHADIRAN & CUTI 
    {
        "key": "grup_kehadiran", "label": "Kehadiran & Cuti", "path": "", "icon": "heroicons:calendar-days", "sort_order": 30,
        "children": [
            {"key": "absensi", "label": "Absensi Harian", "path": "absensi:dashboard", "icon": "heroicons:calendar", "sort_order": 1},
            {"key": "cuti_saya", "label": "Cuti / Izin Saya", "path": "manajemen_cuti:riwayat", "icon": "heroicons:document", "sort_order": 2},
            {"key": "rekap_pribadi", "label": "Rekap Absensi Saya", "path": "absensi:rekap_pribadi", "icon": "heroicons:document-chart-bar", "sort_order": 3},
            {"key": "kelola_cuti", "label": "Kelola Cuti / Izin", "path": "manajemen_cuti:kelola", "icon": "heroicons:clipboard-document-list", "sort_order": 4},
            {"key": "rekap_admin", "label": "Rekap Absensi Admin", "path": "absensi:rekap_admin", "icon": "heroicons:presentation-chart-line", "sort_order": 5},
        ]
    },

    # GRUP: PENUGASAN 
    {
        "key": "grup_penugasan", "label": "Penugasan", "path": "", "icon": "heroicons:briefcase", "sort_order": 40,
        "children": [
            {"key": "schedules_saya", "label": "Jadwal Saya", "path": "schedules:my_schedule", "icon": "heroicons:calendar", "sort_order": 1},
            {"key": "sprin", "label": "Lihat Sprin", "path": "sprin:daftar", "icon": "heroicons:document-text", "sort_order": 2},
            {"key": "schedules_kalender", "label": "Manajemen Jadwal", "path": "schedules:calendar", "icon": "heroicons:calendar-days", "sort_order": 3},
            {"key": "locations", "label": "Wilayah Penugasan", "path": "locations:daftar", "icon": "heroicons:map-pin", "sort_order": 4},
        ]
    },

    # GRUP: PUSAT INFORMASI
    {
        "key": "grup_info", "label": "Pusat Informasi", "path": "", "icon": "heroicons:megaphone", "sort_order": 50,
        "children": [
            {"key": "notifikasi", "label": "Notifikasi", "path": "notifikasi:daftar", "icon": "heroicons:bell", "sort_order": 1},
            {"key": "pengumuman", "label": "Pengumuman", "path": "pengumuman:daftar", "icon": "heroicons:speaker-wave", "sort_order": 2},
        ]
    },

    # GRUP: ADMINISTRATOR
    {
        "key": "grup_admin", "label": "Administrator", "path": "", "icon": "heroicons:shield-check", "sort_order": 60,
        "children": [
            {"key": "personel", "label": "Direktori Personel", "path": "accounts:daftar_personel", "icon": "heroicons:users", "sort_order": 1},
            {"key": "verifikasi", "label": "Verifikasi Akun", "path": "accounts:daftar_verifikasi", "icon": "heroicons:user-plus", "sort_order": 2},
            {"key": "daftar_role", "label": "Manajemen Role", "path": "accounts:daftar_role", "icon": "heroicons:key", "sort_order": 3},
            # Catatan: Fitur manajemen menu dinonaktifkan sesuai permintaan klien.
        ]
    }
]

ROLE_MENU_MAP = {
    "superadmin": [
        "dashboard",
        "grup_kehadiran", "absensi", "cuti_saya", "rekap_pribadi", "kelola_cuti", "rekap_admin",
        "grup_penugasan", "schedules_saya", "sprin", "schedules_kalender", "locations",
        "grup_info", "notifikasi", "pengumuman",
        "grup_admin", "personel", "verifikasi", "daftar_role",
    ],
    "operator": [
        "dashboard", 
        "grup_kehadiran", "absensi", "cuti_saya", "rekap_pribadi", "kelola_cuti", "rekap_admin",
        "grup_penugasan", "sprin", "locations",
        "grup_info", "notifikasi", "pengumuman",
        "grup_admin", "personel", "verifikasi",
    ],
    "pimpinan": [
        "dashboard", 
        "grup_kehadiran", "absensi", "cuti_saya", "rekap_pribadi", "kelola_cuti", "rekap_admin",
        "grup_penugasan", "sprin", "schedules_kalender",
        "grup_info", "notifikasi", "pengumuman",
    ],
    "personel": [
        "dashboard", 
        "grup_kehadiran", "absensi", "cuti_saya", "rekap_pribadi",
        "grup_penugasan", "schedules_saya", "sprin",
        "grup_info", "notifikasi", "pengumuman",
    ],
}

PERSONEL_DATA = [
    {
        "nrp": "80010001", "nama_lengkap": "Admin Utama SIRAGA",
        "pangkat": "Kombespol", "jabatan": "Kepala Sistem Informasi",
        "satker_kode": "NTMC", "role_slug": "superadmin", "password": "siraga2026",
    },
    {
        "nrp": "82020001", "nama_lengkap": "Budi Santoso",
        "pangkat": "Aiptu", "jabatan": "Operator Data Kepegawaian",
        "satker_kode": "BAGRENMIN", "role_slug": "operator", "password": "siraga2026",
    },
    {
        "nrp": "83020002", "nama_lengkap": "Sari Handayani",
        "pangkat": "Bripka", "jabatan": "Operator NTMC",
        "satker_kode": "NTMC", "role_slug": "operator", "password": "siraga2026",
    },
    {
        "nrp": "75030001", "nama_lengkap": "Kombes Andi Wijaya",
        "pangkat": "Kombespol", "jabatan": "Kasubdit Gakkum",
        "satker_kode": "DITGAKKUM", "role_slug": "pimpinan", "password": "siraga2026",
    },
    {
        "nrp": "78030002", "nama_lengkap": "AKBP Rina Marlina",
        "pangkat": "AKBP", "jabatan": "Kabag Operasional",
        "satker_kode": "BAGOPS", "role_slug": "pimpinan", "password": "siraga2026",
    },
    {
        "nrp": "90040001", "nama_lengkap": "Hendra Kusuma",
        "pangkat": "Briptu", "jabatan": "Banit Gakkum",
        "satker_kode": "DITGAKKUM", "role_slug": "personel", "password": "siraga2026",
    },
    {
        "nrp": "91040002", "nama_lengkap": "Dewi Lestari",
        "pangkat": "Bripka", "jabatan": "Banit Kamsel",
        "satker_kode": "SUBDITKAMSEL", "role_slug": "personel", "password": "siraga2026",
    },
    {
        "nrp": "92040003", "nama_lengkap": "Agus Setiawan",
        "pangkat": "Brigpol", "jabatan": "Banit Regident",
        "satker_kode": "SUBDITREGID", "role_slug": "personel", "password": "siraga2026",
    },
    {
        "nrp": "85040004", "nama_lengkap": "Fitri Handayani",
        "pangkat": "Aipda", "jabatan": "Bamin Ops",
        "satker_kode": "BAGOPS", "role_slug": "personel", "password": "siraga2026",
    },
    {
        "nrp": "95040005", "nama_lengkap": "Rudi Hartono",
        "pangkat": "Bripda", "jabatan": "Banit Lantas",
        "satker_kode": "DITLANTAS", "role_slug": "personel", "password": "siraga2026",
    },
]

LOCATION_DATA = [
    # Pos-pos pengamanan lalu lintas
    {
        "name": "Pos Lantas Cikampek KM 42",
        "type": "pos",
        "latitude": -6.4200000,
        "longitude": 107.4530000,
        "radius": 150,
    },
    {
        "name": "Pos Lantas Cawang",
        "type": "pos",
        "latitude": -6.2475000,
        "longitude": 106.8705000,
        "radius": 100,
    },
    {
        "name": "Pos Lantas Tomang",
        "type": "pos",
        "latitude": -6.1802000,
        "longitude": 106.7975000,
        "radius": 100,
    },
    {
        "name": "Pos Lantas Gadog Puncak",
        "type": "pos",
        "latitude": -6.6670000,
        "longitude": 106.8490000,
        "radius": 200,
    },
    {
        "name": "Pos Lantas Brebes Timur",
        "type": "pos",
        "latitude": -6.8713000,
        "longitude": 109.0380000,
        "radius": 150,
    },
    # Mako (Markas Komando)
    {
        "name": "Mako Korlantas Polri",
        "type": "mako",
        "latitude": -6.1862000,
        "longitude": 106.8230000,
        "radius": 250,
    },
    {
        "name": "Mako NTMC Korlantas",
        "type": "mako",
        "latitude": -6.1870000,
        "longitude": 106.8240000,
        "radius": 200,
    },
    {
        "name": "Mako Ditlantas Polda Metro Jaya",
        "type": "mako",
        "latitude": -6.2115000,
        "longitude": 106.8450000,
        "radius": 200,
    },
    # Pos non-aktif (untuk testing filter)
    {
        "name": "Pos Lantas Cikarang Barat (Nonaktif)",
        "type": "pos",
        "latitude": -6.3100000,
        "longitude": 107.1480000,
        "radius": 100,
        "is_active": False,
    },
    {
        "name": "Pos Lantas Karawaci (Nonaktif)",
        "type": "pos",
        "latitude": -6.2570000,
        "longitude": 106.6190000,
        "radius": 100,
        "is_active": False,
    },
]


class Command(BaseCommand):
    help = 'Seed database dengan data dummy untuk testing (akun per role, satker, role object)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Hapus semua data Personel, Satker, Role, dan Lokasi sebelum seeding ulang',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('⚠  Reset: menghapus data lama...'))
            
            # HAPUS DATA TRANSAKSIONAL (CHILD) TERLEBIH DAHULU
            # Ini mengelakkan ProtectedError dari jadual yang merujuk kepada lokasi atau personel
            ShiftSchedule.objects.all().delete()
            
            # (Jika ada model transaksi lain seperti Absensi/Cuti, boleh dipadamkan di sini pada masa hadapan)
            
            # BARU HAPUS DATA MASTER (PARENT)
            Personel.objects.all().delete()
            Satker.objects.all().delete()
            Role.objects.all().delete()
            MenuItem.objects.all().delete()
            Location.objects.all().delete()
            self.stdout.write('   Data dihapus.\n')

        self.stdout.write(self.style.HTTP_INFO('📦 Menyiapkan Satker...'))
        satker_map = {}
        for s in SATKER_DATA:
            obj, created = Satker.objects.get_or_create(
                kode=s['kode'],
                defaults={'nama': s['nama']},
            )
            satker_map[s['kode']] = obj
            status = self.style.SUCCESS('baru') if created else 'sudah ada'
            self.stdout.write(f'   [{status}] {obj.kode} — {obj.nama}')

        self.stdout.write(self.style.HTTP_INFO('\n🛡️ Menyiapkan Role Akses...'))
        role_obj_map = {}
        for r in ROLE_DATA:
            obj, created = Role.objects.get_or_create(
                nama=r['nama'],
                defaults={
                    'display_label': r['display_label'],
                    'deskripsi': r['deskripsi']
                }
            )
            role_obj_map[r['nama']] = obj
            status = self.style.SUCCESS('baru') if created else 'sudah ada'
            self.stdout.write(f'   [{status}] {obj.nama} — {obj.display_label}')

        self.stdout.write(self.style.HTTP_INFO('\n🧭 Menyiapkan Menu Sidebar (Hierarkis)...'))
        menu_map = {}
        for group in MENU_HIERARCHY:
            # 1. Buat Grup / Menu Induk
            parent_obj, created = MenuItem.objects.get_or_create(
                path=group['path'], 
                label=group['label'], # Label dan path sebagai patokan
                defaults={
                    'icon': group['icon'],
                    'sort_order': group['sort_order'],
                    'is_active': True,
                    'parent': None
                },
            )
            menu_map[group['key']] = parent_obj
            status = self.style.SUCCESS('baru') if created else 'sudah ada'
            self.stdout.write(f'   [{status}] {parent_obj.label} (Induk)')

            # 2. Buat Menu Anak untuk Grup Tersebut
            for child in group['children']:
                child_obj, c_created = MenuItem.objects.get_or_create(
                    path=child['path'],
                    defaults={
                        'label': child['label'],
                        'icon': child.get('icon', 'heroicons:chevron-right'),
                        'sort_order': child['sort_order'],
                        'is_active': True,
                        'parent': parent_obj # Kaitkan dengan Induk
                    },
                )
                menu_map[child['key']] = child_obj
                c_status = self.style.SUCCESS('baru') if c_created else 'sudah ada'
                self.stdout.write(f'      ├─ [{c_status}] {child_obj.label} — {child_obj.path}')

        self.stdout.write(self.style.HTTP_INFO('\n🔐 Mengaitkan Menu ke Role...'))
        for role_name, menu_keys in ROLE_MENU_MAP.items():
            role_obj = role_obj_map.get(role_name)
            if not role_obj:
                continue
            menus = [menu_map[key] for key in menu_keys if key in menu_map]
            role_obj.menus.set(menus)
            self.stdout.write(f'   [{self.style.SUCCESS("ok")}] {role_obj.nama} — {len(menus)} menu terhubung')

        self.stdout.write(self.style.HTTP_INFO('\n👤 Menyiapkan Personel...'))
        for p in PERSONEL_DATA:
            if Personel.objects.filter(nrp=p['nrp']).exists():
                self.stdout.write(f'   [sudah ada] {p["nrp"]} — {p["nama_lengkap"]}')
                continue

            satker = satker_map.get(p['satker_kode'])
            role_slug = p['role_slug']
            role_obj = role_obj_map.get(role_slug)

            personel = Personel.objects.create_user(
                nrp=p['nrp'],
                password=p['password'],
                nama_lengkap=p['nama_lengkap'],
                pangkat=p['pangkat'],
                jabatan=p['jabatan'],
                satker=satker,
                role_obj=role_obj,
                is_active = True,
                is_staff=(role_slug == 'superadmin'),
                is_superuser=(role_slug == 'superadmin'),
                status_verifikasi='approved',
            )
            self.stdout.write(
                f'   [{self.style.SUCCESS("baru")}] '
                f'{personel.nrp} — {personel.nama_lengkap} ({role_obj.display_label if role_obj else "Tanpa Role"})'
            )

        self.stdout.write(self.style.HTTP_INFO('\n📍 Menyiapkan Wilayah Penugasan...'))
        for loc in LOCATION_DATA:
            obj, created = Location.objects.get_or_create(
                name=loc['name'],
                defaults={
                    'type': loc['type'],
                    'latitude': loc['latitude'],
                    'longitude': loc['longitude'],
                    'radius': loc['radius'],
                    'is_active': loc.get('is_active', True),
                },
            )
            status = self.style.SUCCESS('baru') if created else 'sudah ada'
            aktif = 'aktif' if obj.is_active else 'nonaktif'
            self.stdout.write(f'   [{status}] {obj.name} ({obj.get_type_display()}, {aktif})')

        self.stdout.write('\n' + '─' * 55)
        self.stdout.write(self.style.SUCCESS('✅ Seeding selesai!'))
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Akun yang tersedia (password: siraga2026):'))
        self.stdout.write('')
        self.stdout.write(f'  {"NRP":<12} {"Nama":<28} {"Role":<12}')
        self.stdout.write(f'  {"─"*12} {"─"*28} {"─"*12}')
        for p in PERSONEL_DATA:
            self.stdout.write(f'  {p["nrp"]:<12} {p["nama_lengkap"]:<28} {p["role_slug"]:<12}')
        self.stdout.write('')
