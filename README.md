# Backlog Yoshelin
- Autentikasi (login/logout)
- Manajemen Profil Personel
- Manajemen Cuti
- Dashboard Monitoring (Overall/ Summary)
- Pengumuman 
# IF-ELSE — Propensi 2025/2026 Genap

Project backend menggunakan **Django** untuk memenuhi persiapan environment pengembangan pada mata kuliah Propensi.

---

# Introduction
SIRAGA adalah sistem informasi terintegrasi untuk NTMC Korlantas Mabes Polri yang digunakan untuk mengelola presensi personel berbasis geolocation sesuai sprin aktif, pengajuan dan persetujuan cuti secara digital, serta menyediakan rekapitulasi dan dashboard monitoring untuk pimpinan/SDM agar pengelolaan administrasi personel lebih akurat, transparan, dan berbasis data.

---

# Struktur Repository

```
if-else
│
├── config/           # konfigurasi utama Django (settings, urls, wsgi, asgi)
├── manage.py         # command utama untuk menjalankan Django
├── requirements.txt  # daftar dependency Python
├── docs/             # dokumentasi fitur / backlog tiap anggota
└── README.md         # panduan instalasi dan penggunaan project
```

---

# Prasyarat

Pastikan perangkat sudah memiliki:

* Python3 (disarankan Python 3.10+)
* Git
* Terminal/ Command Line

Cek versi Python:

```
python3 --version
```

---

# Cara Instalasi dan Menjalankan Project

### 1. Clone Repository

```
git clone https://gitlab.cs.ui.ac.id/propensi-2025-2026-genap/kelas-c/if-else/if-else.git
cd if-else
```

### 2. Membuat Virtual Environment

```
python3 -m venv venv
```

### 3. Mengaktifkan Virtual Environment

Mac / Linux:

```
source venv/bin/activate
```

Windows:

```
venv\Scripts\activate
```

---

### 4. Install Dependency

```
python -m pip install -r requirements.txt
```

---

### 5. Jalankan Migrasi Database

```
python manage.py migrate
```

Ini akan membuat database default Django.

---

### 6. Menjalankan Server

```
python manage.py runserver
```

Kemudian, buka di browser:

```
http://127.0.0.1:8000
```

Jika berhasil, akan muncul halaman default Django yang menandakan run berhasil.

---

# Git Workflow

Repository menggunakan struktur branch berikut:

```
main
development
staging
feature-{nama-anggota}
```

Penjelasan:

* **main** → versi stabil / production
* **development** → integrasi fitur sebelum staging
* **staging** → testing sebelum demo
* **feature-{nama-anggota}** → branch individu setiap anggota

Pada repositori kami, branch individunya adalah:

```
feature-yoshelin
feature-wahyu
feature-gandes
```

---


# Kontribusi Anggota

Setiap anggota bekerja pada branch masing-masing dan membuat Merge Request ke branch `development`.

Contoh branch individu:

```
feature-yoshelin
feature-wahyu
feature-gandes
```

---

# Additional: Troubleshooting

Jika muncul error dependency:

```
python -m pip install -r requirements.txt
```

Jika virtual environment tidak aktif:

```
source venv/bin/activate
```

Jika migrasi belum dijalankan:

```
python manage.py migrate
```

---

# Additional: Jika Ingin Membuat Admin Django

```
python manage.py createsuperuser
```

Setelah itu login di:

```
http://127.0.0.1:8000/admin
```

---

# Catatan

Project ini merupakan template awal Django yang digunakan untuk memenuhi persiapan environment pengembangan pada mata kuliah **Propensi**.
