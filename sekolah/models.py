import mimetypes
import uuid
import os
import random
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


def validate_image_extension(value):
    # 1. Cek Ukuran (Batas 5 MB)
    if value.size > 5 * 1024 * 1024:  
        raise ValidationError('Ukuran gambar tidak boleh lebih dari 5 MB!')

    # 2. Cek Ekstensi Nama File
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError('Format gambar tidak didukung! Gunakan format: .jpg, .jpeg, .png, atau .webp')

    # 3. PERBAIKAN: Cek MIME Type dasar untuk memastikan file tidak dikamuflase
    mime_type, _ = mimetypes.guess_type(value.name)
    if not mime_type or not mime_type.startswith('image/'):
        raise ValidationError('File yang diunggah terdeteksi bukan sebagai gambar yang valid (Kemungkinan file dikamuflase).')


def validate_pdf_extension(value):
    # 1. Cek Ukuran (Batas 10 MB)
    if value.size > 10 * 1024 * 1024:  
        raise ValidationError('Ukuran lampiran tidak boleh lebih dari 10 MB!')

    # 2. Cek Ekstensi
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError('Lampiran harus berupa file PDF atau Gambar!')

    # 3. PERBAIKAN: Cek MIME Type dasar
    mime_type, _ = mimetypes.guess_type(value.name)
    valid_mimes = ['application/pdf', 'image/jpeg', 'image/png', 'image/webp']
    if not mime_type or mime_type not in valid_mimes:
        raise ValidationError('Tipe konten file tidak sesuai dengan ekstensi yang diizinkan.')


def ubah_nama_foto_sdm(instance, filename):
    ext = filename.split('.')[-1].lower()
    nama_acak = f"{uuid.uuid4()}.{ext}"
    return os.path.join('sdm/', nama_acak)


class Guru(models.Model):
    KATEGORI_CHOICES = [
        ('Pimpinan', 'Pimpinan (Kepala/Wakil Sekolah)'),
        ('Wali Kelas', 'Wali Kelas'),
        ('Guru Mata Pelajaran', 'Guru Mata Pelajaran'),
        ('Tahsin & Tahfidz', 'Tahsin & Tahfidz'),
        ('Staf & TU', 'Staf & Tata Usaha'),
        ('Office Boy', 'Office Boy (OB)'),
    ]

    user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='guru_profile',
        help_text="Akun user Django yang terhubung dengan data SDM ini"
    )

    nama = models.CharField(max_length=100)
    gelar = models.CharField(max_length=50, blank=True, null=True, help_text="Contoh: S.T., S.Kom., M.Pd.")
    nip = models.CharField(max_length=50, blank=True, null=True, help_text="NIP / NIY pegawai")
    
    pendidikan_terakhir = models.CharField(max_length=50, blank=True, null=True, help_text="Contoh: S1, S2, D3")
    asal_kampus = models.CharField(max_length=150, blank=True, null=True, help_text="Contoh: Universitas Pasundan, UPI, dll")
    
    jabatan = models.CharField(max_length=100, help_text="Contoh: Kepala Sekolah, Wali Kelas 1A, dll")
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES, default='Guru Mata Pelajaran')
    mapel = models.CharField(max_length=150, blank=True, null=True, help_text="Mata pelajaran / Bidang tugas")
    motto = models.TextField(blank=True, null=True, help_text="Motto atau kutipan kerja")
    foto = models.ImageField(
        upload_to=ubah_nama_foto_sdm, 
        validators=[validate_image_extension], 
        blank=True, 
        null=True, 
        default='default-profile/profile-picture.png'
    )
    
    role = models.IntegerField(default=1, help_text="Urutan ID/Role: 1 (Kepala Sekolah), 2 (Wakil/Koordinator), dst.")
    
    badge_color = models.CharField(
        max_length=100, 
        default='bg-blue-900 text-amber-300', 
        help_text="Class Tailwind untuk warna badge"
    )

    class Meta:
        ordering = ['role', 'nama'] 
        verbose_name = "SDM (Guru & Staf)"
        verbose_name_plural = "Data SDM (Guru & Staf)"

    def __str__(self):
        gelar_str = f", {self.gelar}" if self.gelar else ""
        user_str = f" [User: {self.user.username}]" if self.user else " [Tanpa Akun User]"
        return f"[{self.role}] {self.nama}{gelar_str} - {self.jabatan}{user_str}"


def ubah_nama_gambar_acak(instance, filename):
    ext = filename.split('.')[-1].lower()
    nama_acak = f"{uuid.uuid4()}.{ext}"
    return os.path.join('berita/', nama_acak)


class Berita(models.Model):
    KATEGORI_CHOICES = [
        ('Kegiatan Siswa', 'Kegiatan Siswa'),
        ('Prestasi', 'Prestasi'),
        ('Akademik', 'Akademik'),
        ('Pengumuman', 'Pengumuman'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judul = models.CharField(max_length=200)
    ringkasan = models.TextField(help_text="Ringkasan singkat untuk ditampilkan di kartu berita", blank=True, null=True)
    isi = models.TextField(help_text="Isi berita lengkap (mendukung HTML / Rich Text)")
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES, default='Kegiatan Siswa')
    gambar = models.ImageField(upload_to=ubah_nama_gambar_acak, validators=[validate_image_extension], blank=True, null=True)
    is_featured = models.BooleanField(default=False, help_text="Tandai sebagai berita utama (headline)")
    penulis = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='berita_list',
        help_text="User/Penulis yang mengunggah berita ini"
    )
    tanggal_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal_upload']
        verbose_name = "Berita & Kegiatan"
        verbose_name_plural = "Data Berita & Kegiatan"

    def __str__(self):
        return self.judul
    
    
def ubah_nama_file_pengumuman(instance, filename):
    ext = filename.split('.')[-1].lower()
    nama_acak = f"{uuid.uuid4()}.{ext}"
    return os.path.join('pengumuman/lampiran/', nama_acak)


class Pengumuman(models.Model):
    KATEGORI_CHOICES = [
        ('Surat Edaran', 'Surat Edaran'),
        ('Akademik & Ujian', 'Akademik & Ujian'),
        ('Kegiatan', 'Kegiatan'),
        ('Keuangan', 'Keuangan'),
    ]
    
    PRIORITAS_CHOICES = [
        ('Mendesak', 'Mendesak'),
        ('Penting', 'Penting'),
        ('Biasa', 'Biasa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judul = models.CharField(max_length=200)
    ringkasan = models.TextField(help_text="Ringkasan singkat untuk kartu pengumuman", blank=True, null=True)
    isi_pengumuman = models.TextField(help_text="Isi pengumuman lengkap")
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES, default='Surat Edaran')
    prioritas = models.CharField(max_length=20, choices=PRIORITAS_CHOICES, default='Biasa')
    tanggal = models.DateField(help_text="Tanggal pengumuman diterbitkan")
    target = models.CharField(max_length=150, default="Wali Murid & Siswa", help_text="Target pembaca/audiens")
    lampiran = models.FileField(upload_to=ubah_nama_file_pengumuman, validators=[validate_pdf_extension], blank=True, null=True, help_text="File lampiran PDF (opsional)")
    is_pinned = models.BooleanField(default=False, help_text="Tandai sebagai pengumuman disematkan (pinned)")
    tanggal_dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-tanggal', '-tanggal_dibuat']
        verbose_name = "Pengumuman"
        verbose_name_plural = "Data Pengumuman"

    def __str__(self):
        return self.judul


class ProfilSekolah(models.Model):
    nama_sekolah = models.CharField(max_length=100, default="Nama Sekolah")
    sejarah = models.TextField(help_text="Tuliskan sejarah singkat sekolah")
    visi = models.TextField()
    misi = models.TextField(help_text="Gunakan enter untuk memisahkan setiap poin misi")
    
    def __str__(self):
        return self.nama_sekolah


class HeroBanner(models.Model):
    tag = models.CharField(max_length=50, default="Selamat Datang", help_text="Teks kecil di atas judul")
    judul = models.CharField(max_length=200, default="SD YWKA REL HOMY SCHOOL")
    isi = models.TextField(help_text="Deskripsi atau teks paragraf di bawah judul")
    gambar = models.ImageField(upload_to='hero/', validators=[validate_image_extension], null=True, blank=True)
    link = models.CharField(max_length=200, default="/profil")
    teks_tombol = models.CharField(max_length=50, default="Mulai Mengenal Kami")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.judul


class AlbumGaleri(models.Model):
    KATEGORI_CHOICES = [
        ('Prestasi & Lomba', 'Prestasi & Lomba'),
        ('MPLS & Orientasi', 'MPLS & Orientasi'),
        ('Keagamaan', 'Keagamaan'),
        ('Ekskul & Seni', 'Ekskul & Seni'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judul = models.CharField(max_length=200)
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES, default='Prestasi & Lomba')
    tanggal = models.DateField(help_text="Tanggal kegiatan album")
    cover = models.ImageField(upload_to='galeri/cover/', validators=[validate_image_extension], blank=True, null=True, help_text="Foto sampul album")
    deskripsi = models.TextField(blank=True, null=True, help_text="Deskripsi singkat album kegiatan")
    tanggal_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal', '-tanggal_upload']
        verbose_name = "Album Galeri Foto"
        verbose_name_plural = "Data Album Galeri Foto"

    def __str__(self):
        return self.judul


def ubah_nama_foto_album(instance, filename):
    ext = filename.split('.')[-1].lower()
    nama_acak = f"{uuid.uuid4()}.{ext}"
    return os.path.join('galeri/foto_item/', nama_acak)


class FotoAlbum(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    album = models.ForeignKey(AlbumGaleri, related_name='fotos', on_delete=models.CASCADE, help_text="Pilih album induk")
    gambar = models.ImageField(upload_to=ubah_nama_foto_album, validators=[validate_image_extension])
    keterangan = models.CharField(max_length=255, blank=True, null=True, help_text="Keterangan opsional untuk foto ini")

    class Meta:
        verbose_name = "Foto Item Album"
        verbose_name_plural = "Data Foto Item Album"

    def __str__(self):
        return f"Foto dalam Album: {self.album.judul}"


class VideoGaleri(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judul = models.CharField(max_length=200)
    kategori = models.CharField(max_length=50, choices=AlbumGaleri.KATEGORI_CHOICES, default='MPLS & Orientasi')
    tanggal = models.DateField(help_text="Tanggal video diterbitkan")
    embed_url = models.URLField(help_text="URL Embed YouTube (contoh: https://www.youtube.com/embed/...)")
    tanggal_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal', '-tanggal_upload']
        verbose_name = "Video Dokumentasi"
        verbose_name_plural = "Data Video Dokumentasi"

    def __str__(self):
        return self.judul


def ubah_nama_foto_profil(instance, filename):
    ext = filename.split('.')[-1].lower()
    nama_acak = f"{uuid.uuid4()}.{ext}"
    return os.path.join('profil_users/', nama_acak)


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('guru', 'Guru / Pengajar'),
        ('staf', 'Staf / Tata Usaha'),
        ('user', 'User Biasa'),
    ]

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profil',
        help_text="Akun user Django yang terhubung dengan profil ini"
    )
    foto_profil = models.ImageField(
        upload_to=ubah_nama_foto_profil, 
        validators=[validate_image_extension], 
        blank=True, 
        null=True, 
        default='default-profile/profile-picture.png',
        help_text="Foto profil akun (avatar)"
    )
    motto = models.TextField(blank=True, null=True, help_text="Motto atau quotes pribadi user")
    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guru', help_text="Role portal sekunder pengguna")
    uuid_code = models.CharField(max_length=6, unique=True, null=True, blank=True, help_text="Kode UUID unik 6 angka random untuk presensi digital")

    def __str__(self):
        return f"Profil dari {self.user.username} ({self.role_type})"


class Presensi(models.Model):
    STATUS_CHOICES = [
        ('Hadir Tepat Waktu', 'Hadir Tepat Waktu'),
        ('Terlambat', 'Terlambat'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='riwayat_presensi')
    waktu_scan = models.DateTimeField(auto_now_add=True)
    waktu_pulang = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Hadir Tepat Waktu')
    peran = models.CharField(max_length=50, default='Guru')

    class Meta:
        ordering = ['-waktu_scan']
        verbose_name = "Presensi Kehadiran"
        verbose_name_plural = "Data Riwayat Presensi"

    def __str__(self):
        pulang_str = f" | Pulang: {self.waktu_pulang.strftime('%H:%M:%S')}" if self.waktu_pulang else ""
        return f"{self.user.username} - Masuk: {self.waktu_scan.strftime('%Y-%m-%d %H:%M:%S')}{pulang_str} ({self.status})"


def ubah_nama_poster_event(instance, filename):
    ext = filename.split('.')[-1].lower()
    nama_acak = f"{uuid.uuid4()}.{ext}"
    return os.path.join('event/poster/', nama_acak)


class Event(models.Model):
    KATEGORI_CHOICES = [
        ('Akademik', 'Akademik & Ujian'),
        ('Keagamaan', 'Keagamaan & PHBI'),
        ('Seni & Olahraga', 'Seni & Olahraga'),
        ('Peringatan Hari Besar', 'Peringatan Hari Besar'),
        ('Rapat & Pertemuan', 'Rapat & Pertemuan'),
        ('Lainnya', 'Lainnya'),
    ]

    STATUS_CHOICES = [
        ('Akan Datang', 'Akan Datang'),
        ('Berlangsung', 'Berlangsung'),
        ('Selesai', 'Selesai'),
        ('Dibatalkan', 'Dibatalkan'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judul = models.CharField(max_length=200)
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES, default='Akademik')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Akan Datang')
    tanggal_mulai = models.DateField(help_text="Tanggal mulai acara")
    tanggal_selesai = models.DateField(blank=True, null=True, help_text="Tanggal selesai (opsional jika 1 hari)")
    waktu = models.CharField(max_length=100, default="08:00 WIB - Selesai", help_text="Contoh: 08:00 - 12:00 WIB")
    lokasi = models.CharField(max_length=200, default="SD YWKA", help_text="Lokasi / Tempat Acara")
    penyelenggara = models.CharField(max_length=150, default="SD YWKA", help_text="Penyelenggara / Panitia Acara")
    ringkasan = models.TextField(blank=True, null=True, help_text="Ringkasan singkat untuk kartu acara")
    deskripsi = models.TextField(help_text="Deskripsi lengkap / susunan acara")
    poster = models.ImageField(upload_to=ubah_nama_poster_event, validators=[validate_image_extension], blank=True, null=True)
    link_pendaftaran = models.URLField(blank=True, null=True, help_text="Link pendaftaran / Google Form (opsional)")
    is_featured = models.BooleanField(default=False, help_text="Tandai sebagai acara utama / unggulan")
    tanggal_dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal_mulai', '-tanggal_dibuat']
        verbose_name = "Event & Acara"
        verbose_name_plural = "Data Event & Acara"

    def __str__(self):
        return f"{self.judul} ({self.tanggal_mulai})"


def ubah_nama_foto_post(instance, filename):
    ext = filename.split('.')[-1].lower()
    nama_acak = f"{uuid.uuid4()}.{ext}"
    return os.path.join('posts/', nama_acak)


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_posts')
    gambar = models.ImageField(upload_to=ubah_nama_foto_post, validators=[validate_image_extension], blank=True, null=True)
    caption = models.TextField(blank=True, null=True)
    tanggal_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal_upload']
        verbose_name = "Postingan Pengguna"
        verbose_name_plural = "Data Postingan Pengguna"

    def __str__(self):
        return f"Post oleh {self.user.username} ({self.tanggal_upload.strftime('%d-%m-%Y')})"


class PostLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} menyukai post {self.post.id}"


class PostComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_comments')
    teks = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Komentar oleh {self.user.username} pada post {self.post.id}"


class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notes')
    teks = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Status / Note Teks"
        verbose_name_plural = "Data Status / Note Teks"

    def __str__(self):
        return f"Note oleh {self.user.username}: {self.teks[:30]}"


class NoteLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_note_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('note', 'user')

    def __str__(self):
        return f"{self.user.username} menyukai note {self.note.id}"