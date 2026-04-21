from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

class MenuItem(models.Model):
    label = models.CharField(max_length=100, verbose_name='Label')
    path = models.CharField(max_length=200, blank=True, verbose_name='Path / URL Name')
    icon = models.CharField(max_length=100, blank=True, verbose_name='Icon')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, 
        related_name='submenus', verbose_name='Parent Menu'
    )
    sort_order = models.IntegerField(default=0, verbose_name='Sort Order')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    class Meta:
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'
        ordering = ['sort_order', 'label']

    def __str__(self):
        return f"{self.label} ({self.path})"
    
    def get_url(self):
        try:
            return reverse(self.path)
        except NoReverseMatch:
            return self.path
    
class Role(models.Model):
    nama = models.CharField(max_length=100, unique=True, verbose_name='Nama Role')
    deskripsi = models.TextField(blank=True, verbose_name='Deskripsi')
    dibuat_pada = models.DateTimeField(default=timezone.now, verbose_name='Dibuat Pada')
    menus = models.ManyToManyField(MenuItem, blank=True, related_name='roles', verbose_name='Menu Access')
    display_label = models.CharField(max_length=100, blank=True, verbose_name='Display Label')

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
    def is_pimpinan(self):
        if self.role_obj:
            return self.role_obj.nama.lower() == 'pimpinan'
        return self.role == 'pimpinan'

    @property
    def is_operator(self):
        if self.role_obj:
            return self.role_obj.nama.lower() == 'operator'
        return self.role == 'operator'

    @property
    def is_superadmin(self):
        if self.role_obj:
            return self.role_obj.nama.lower() == 'superadmin'
        return self.role == 'superadmin'
    
    def save(self, *args, **kwargs):
        if self.role_obj:
            self.role = self.role_obj.nama.lower()
        
        super(Personel, self).save(*args, **kwargs)