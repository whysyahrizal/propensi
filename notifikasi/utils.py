"""
PBI-047 — Email Notifikasi
Utility untuk membuat notifikasi + mengirim email.

Penggunaan:
    from notifikasi.utils import kirim_notifikasi

    kirim_notifikasi(
        user=request.user,
        judul='Pengajuan Cuti Disetujui',
        pesan='Pengajuan cuti Anda telah disetujui oleh pimpinan.',
        tipe='cuti',
        link='/cuti/detail/1/',
    )
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def kirim_notifikasi(user, judul, pesan, tipe='info', link='', kirim_email=True):
    """
    Buat notifikasi untuk user dan opsional kirim email.

    Args:
        user: instance accounts.Personel (penerima)
        judul: str, judul notifikasi
        pesan: str, isi notifikasi
        tipe: str, salah satu dari 'info'|'cuti'|'sprin'|'presensi'|'jadwal'|'sistem'
        link: str, URL relatif menuju halaman terkait (opsional)
        kirim_email: bool, apakah email juga dikirim (default True)

    Returns:
        Notifikasi instance yang baru dibuat
    """
    from .models import Notifikasi

    notif = Notifikasi.objects.create(
        user=user,
        judul=judul,
        pesan=pesan,
        tipe=tipe,
        link=link,
    )

    if kirim_email and user.email:
        _kirim_email_notifikasi(notif)

    return notif


def kirim_notifikasi_massal(users, judul, pesan, tipe='info', link='', kirim_email=True):
    """
    Kirim notifikasi ke banyak user sekaligus (bulk).

    Args:
        users: queryset atau list accounts.Personel
        Argumen lain sama dengan kirim_notifikasi()
    """
    notifikasi_list = []
    for user in users:
        notif = kirim_notifikasi(
            user=user,
            judul=judul,
            pesan=pesan,
            tipe=tipe,
            link=link,
            kirim_email=kirim_email,
        )
        notifikasi_list.append(notif)
    return notifikasi_list


def _kirim_email_notifikasi(notif):
    """
    Kirim email untuk satu Notifikasi instance.
    Kegagalan dicatat ke log tetapi TIDAK meng-crash proses utama (PBI-047).
    """
    try:
        subject = f"[SIRAGA] {notif.judul}"

        # Bangun isi email plain text
        site_name = getattr(settings, 'SIRAGA_SITE_NAME', 'SIRAGA Korlantas')
        base_url = getattr(settings, 'SIRAGA_BASE_URL', 'http://localhost:8000')

        body_lines = [
            f"Halo, {notif.user.nama_lengkap},",
            "",
            notif.pesan,
        ]

        if notif.link:
            full_link = f"{base_url}{notif.link}"
            body_lines += [
                "",
                "Lihat detail selengkapnya:",
                full_link,
            ]

        body_lines += [
            "",
            "—",
            f"Sistem Informasi {site_name}",
            "Email ini dikirim otomatis, harap tidak membalas.",
        ]

        send_mail(
            subject=subject,
            message="\n".join(body_lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notif.user.email],
            fail_silently=False,
        )

        # Catat log pengiriman (PBI-047)
        notif.email_terkirim = True
        notif.email_dikirim_pada = timezone.now()
        notif.save(update_fields=['email_terkirim', 'email_dikirim_pada'])

        logger.info(f"[notifikasi] Email terkirim ke {notif.user.email} — '{notif.judul}'")

    except Exception as exc:
        # Tangani kegagalan secara minimal tanpa menghentikan proses utama (PBI-047)
        logger.error(
            f"[notifikasi] Gagal mengirim email ke {notif.user.email} — "
            f"'{notif.judul}': {exc}"
        )
