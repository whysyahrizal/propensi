from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class Role(models.Model):

    nama = models.CharField(max_length=100, unique=True, verbose_name='Nama Role')
    deskripsi = models.TextField(blank=True, verbose_name='Deskripsi')
    dibuat_pada = models.DateTimeField(default=timezone.now, verbose_name='Dibuat Pada')

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Role'
        ordering = ['nama']

    def __str__(self):
        return self.nama

    def jumlah_pengguna(self):
        return self.personel_set.filter(is_active=True).count()

class Satker(models.Model):
    nama = models.CharField(max_length=200)
    kode = models.CharField(max_length=20, unique=True)
    keterangan = models.TextField(blank=True)

    class Meta:
        verbose_name = "Satuan Kerja"
        verbose_name_plural = "Satuan Kerja"
        ordering = ['nama']

    def __str__(self):
        return f"{self.kode} - {self.nama}"

class PersonelManager(BaseUserManager):
    def create_user(self, nrp, password=None, **extra_fields):
        if not nrp:
            raise ValueError('NRP harus diisi')
        user = self.model(nrp=nrp, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nrp, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')
        return self.create_user(nrp, password, **extra_fields)

class Personel(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('personel', 'Personel'),
        ('operator', 'Operator'),
        ('pimpinan', 'Pimpinan'),
        ('superadmin', 'Superadmin'),
    ]

    PANGKAT_CHOICES = [
        ('Bharada', 'Bharada'),
        ('Bhayangkara', 'Bhayangkara'),
        ('Bripda', 'Bripda'),
        ('Briptu', 'Briptu'),
        ('Brigpol', 'Brigpol'),
        ('Bripka', 'Bripka'),
        ('Aipda', 'Aipda'),
        ('Aiptu', 'Aiptu'),
        ('Ipda', 'Ipda'),
        ('Iptu', 'Iptu'),
        ('AKP', 'AKP'),
        ('Kompol', 'Kompol'),
        ('AKBP', 'AKBP'),
        ('Kombespol', 'Kombespol'),
        ('Brigjen Pol', 'Brigjen Pol'),
        ('Irjen Pol', 'Irjen Pol'),
        ('Komjen Pol', 'Komjen Pol'),
        ('Jenderal Pol', 'Jenderal Pol'),
    ]

    nrp = models.CharField(max_length=20, unique=True, verbose_name='NRP')
    nama_lengkap = models.CharField(max_length=200, verbose_name='Nama Lengkap')
    email = models.EmailField(blank=True, verbose_name='Email')
    no_hp = models.CharField(max_length=20, blank=True, verbose_name='No. HP')
    pangkat = models.CharField(max_length=50, choices=PANGKAT_CHOICES, blank=True, verbose_name='Pangkat')
    jabatan = models.CharField(max_length=200, blank=True, verbose_name='Jabatan')
    satker = models.ForeignKey(
        Satker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='personel', verbose_name='Satuan Kerja'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='personel', verbose_name='Role')
    role_obj = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='personel_set', verbose_name='Role (Object)'
    )
    foto = models.ImageField(upload_to='foto_personel/', blank=True, null=True, verbose_name='Foto')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    tanggal_bergabung = models.DateTimeField(auto_now_add=True)

    tanggal_nonaktif = models.DateTimeField(null=True, blank=True, verbose_name='Tanggal Dinonaktifkan')
    alasan_nonaktif = models.TextField(blank=True, verbose_name='Alasan Dinonaktifkan')

    objects = PersonelManager()

    USERNAME_FIELD = 'nrp'
    REQUIRED_FIELDS = ['nama_lengkap']

    class Meta:
        verbose_name = 'Personel'
        verbose_name_plural = 'Personel'
        ordering = ['nama_lengkap']

    def __str__(self):
        return f"{self.pangkat} {self.nama_lengkap} ({self.nrp})"

    @property
    def nama_pangkat(self):
        return f"{self.pangkat} {self.nama_lengkap}".strip()

    @property
    def is_pimpinan(self):
        return self.role == 'pimpinan'

    @property
    def is_operator(self):
        return self.role == 'operator'

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
