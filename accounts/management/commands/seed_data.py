"""
Management command: seed_data
Mengisi database dengan data dummy untuk keperluan testing.

Jalankan dengan:
    python manage.py seed_data
    python manage.py seed_data --reset   # hapus data sebelumnya dulu
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import Personel, Satker, Role


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
    {"nama": "Superadmin",  "deskripsi": "Akses penuh ke seluruh fitur dan pengaturan sistem SIRAGA."},
    {"nama": "Operator",    "deskripsi": "Mengelola data personel, sprin, dan pengumuman. Tidak dapat menyetujui cuti."},
    {"nama": "Pimpinan",    "deskripsi": "Menyetujui atau menolak pengajuan cuti personel di bawah satker yang sama."},
    {"nama": "Personel",    "deskripsi": "Melakukan presensi harian, mengajukan cuti, dan melihat sprin yang ditugaskan."},
]

PERSONEL_DATA = [
    # Superadmin
    {
        "nrp": "SUPER001", "nama_lengkap": "Admin Utama SIRAGA",
        "pangkat": "Kombespol", "jabatan": "Kepala Sistem Informasi",
        "satker_kode": "NTMC", "role": "superadmin", "password": "siraga2026",
    },
    # Operator
    {
        "nrp": "OPR001", "nama_lengkap": "Budi Santoso",
        "pangkat": "Aiptu", "jabatan": "Operator Data Kepegawaian",
        "satker_kode": "BAGRENMIN", "role": "operator", "password": "siraga2026",
    },
    {
        "nrp": "OPR002", "nama_lengkap": "Sari Handayani",
        "pangkat": "Bripka", "jabatan": "Operator NTMC",
        "satker_kode": "NTMC", "role": "operator", "password": "siraga2026",
    },
    # Pimpinan
    {
        "nrp": "PIM001", "nama_lengkap": "Kombes Andi Wijaya",
        "pangkat": "Kombespol", "jabatan": "Kasubdit Gakkum",
        "satker_kode": "DITGAKKUM", "role": "pimpinan", "password": "siraga2026",
    },
    {
        "nrp": "PIM002", "nama_lengkap": "AKBP Rina Marlina",
        "pangkat": "AKBP", "jabatan": "Kabag Operasional",
        "satker_kode": "BAGOPS", "role": "pimpinan", "password": "siraga2026",
    },
    # Personel
    {
        "nrp": "PRS001", "nama_lengkap": "Hendra Kusuma",
        "pangkat": "Briptu", "jabatan": "Banit Gakkum",
        "satker_kode": "DITGAKKUM", "role": "personel", "password": "siraga2026",
    },
    {
        "nrp": "PRS002", "nama_lengkap": "Dewi Lestari",
        "pangkat": "Bripka", "jabatan": "Banit Kamsel",
        "satker_kode": "SUBDITKAMSEL", "role": "personel", "password": "siraga2026",
    },
    {
        "nrp": "PRS003", "nama_lengkap": "Agus Setiawan",
        "pangkat": "Brigadir", "jabatan": "Banit Regident",
        "satker_kode": "SUBDITREGID", "role": "personel", "password": "siraga2026",
    },
    {
        "nrp": "PRS004", "nama_lengkap": "Fitri Handayani",
        "pangkat": "Aipda", "jabatan": "Bamin Ops",
        "satker_kode": "BAGOPS", "role": "personel", "password": "siraga2026",
    },
    {
        "nrp": "PRS005", "nama_lengkap": "Rudi Hartono",
        "pangkat": "Bripda", "jabatan": "Banit Lantas",
        "satker_kode": "DITLANTAS", "role": "personel", "password": "siraga2026",
    },
]


class Command(BaseCommand):
    help = 'Seed database dengan data dummy untuk testing (akun per role, satker, role object)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Hapus semua data Personel, Satker, dan Role sebelum seeding ulang',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('⚠  Reset: menghapus data lama...'))
            Personel.objects.all().delete()
            Satker.objects.all().delete()
            Role.objects.all().delete()
            self.stdout.write('   Data dihapus.\n')

        # 1. Buat Satker
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

        # 2. Buat Role (object)
        self.stdout.write(self.style.HTTP_INFO('\n🔐 Menyiapkan Role...'))
        role_obj_map = {}
        for r in ROLE_DATA:
            obj, created = Role.objects.get_or_create(
                nama=r['nama'],
                defaults={'deskripsi': r['deskripsi']},
            )
            role_obj_map[r['nama'].lower()] = obj
            status = self.style.SUCCESS('baru') if created else 'sudah ada'
            self.stdout.write(f'   [{status}] {obj.nama}')

        # 3. Buat Personel
        self.stdout.write(self.style.HTTP_INFO('\n👤 Menyiapkan Personel...'))
        for p in PERSONEL_DATA:
            if Personel.objects.filter(nrp=p['nrp']).exists():
                self.stdout.write(f'   [sudah ada] {p["nrp"]} — {p["nama_lengkap"]}')
                continue

            satker = satker_map.get(p['satker_kode'])
            role_key = p['role']
            # Cari role object yang cocok
            role_obj = None
            for key, obj in role_obj_map.items():
                if key.startswith(role_key):
                    role_obj = obj
                    break

            personel = Personel.objects.create_user(
                nrp=p['nrp'],
                password=p['password'],
                nama_lengkap=p['nama_lengkap'],
                pangkat=p['pangkat'],
                jabatan=p['jabatan'],
                satker=satker,
                role=role_key,
                role_obj=role_obj,
                is_staff=(role_key == 'superadmin'),
                is_superuser=(role_key == 'superadmin'),
            )
            self.stdout.write(
                f'   [{self.style.SUCCESS("baru")}] '
                f'{personel.nrp} — {personel.nama_lengkap} ({personel.get_role_display()})'
            )

        # Summary
        self.stdout.write('\n' + '─' * 55)
        self.stdout.write(self.style.SUCCESS('✅ Seeding selesai!'))
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Akun yang tersedia (password: siraga2026):'))
        self.stdout.write('')
        self.stdout.write(f'  {"NRP":<12} {"Nama":<28} {"Role":<12}')
        self.stdout.write(f'  {"─"*12} {"─"*28} {"─"*12}')
        for p in PERSONEL_DATA:
            self.stdout.write(f'  {p["nrp"]:<12} {p["nama_lengkap"]:<28} {p["role"]:<12}')
        self.stdout.write('')
