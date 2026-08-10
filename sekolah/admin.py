# FILE: sekolah/admin.py
from django.contrib import admin
from .models import Guru, Berita, AlbumGaleri, FotoAlbum, VideoGaleri, Pengumuman, ProfilSekolah, HeroBanner

@admin.register(Guru)
class GuruAdmin(admin.ModelAdmin):
    list_display = ('role', 'nama', 'jabatan', 'kategori', 'nip')
    list_editable = ('role',)
    list_display_links = ('nama',)
    list_filter = ('kategori', 'role')
    search_fields = ('nama', 'jabatan', 'mapel', 'nip')

@admin.register(Berita)
class BeritaAdmin(admin.ModelAdmin):
    list_display = ('judul', 'tanggal_upload')
    search_fields = ('judul',)

class FotoAlbumInline(admin.TabularInline):
    model = FotoAlbum
    extra = 3

@admin.register(AlbumGaleri)
class AlbumGaleriAdmin(admin.ModelAdmin):
    inlines = [FotoAlbumInline]
    list_display = ('judul', 'kategori', 'tanggal', 'tanggal_upload')
    list_filter = ('kategori', 'tanggal')
    search_fields = ('judul', 'deskripsi')

@admin.register(VideoGaleri)
class VideoGaleriAdmin(admin.ModelAdmin):
    list_display = ('judul', 'kategori', 'tanggal', 'tanggal_upload')
    list_filter = ('kategori', 'tanggal')
    search_fields = ('judul',)

@admin.register(Pengumuman)
class PengumumanAdmin(admin.ModelAdmin):
    list_display = ('judul', 'tanggal_dibuat')

@admin.register(ProfilSekolah)
class ProfilSekolahAdmin(admin.ModelAdmin):
    list_display = ('nama_sekolah', 'visi')

@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ('judul', 'tag', 'is_active')
    list_filter = ('is_active',)