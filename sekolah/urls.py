from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # API Publik (Guest)
    path('guru/', views.get_guru, name='get_guru'),
    path('guru/<int:pk>/', views.get_guru_detail, name='get_guru_detail'),
    path('berita/', views.get_berita, name='get_berita'),
    path('berita/<str:pk>/', views.get_berita_detail, name='get_berita_detail'),
    path('galeri/', views.get_galeri, name='get_galeri'),
    path('pengumuman/', views.get_pengumuman, name='get_pengumuman'),
    path('pengumuman/<str:pk>/', views.get_pengumuman_detail, name='get_pengumuman_detail'),
    path('profil/', views.get_profil, name='get_profil'),
    path('susunan-organisasi/', views.get_susunan_organisasi, name='get_susunan_organisasi'),
    path('hero/', views.get_hero, name='get_hero'),

    # Admin Dashboard API
    path('admin-api/dashboard-stats/', views.admin_dashboard_stats, name='admin_dashboard_stats'),
    
    # Admin Presensi APIs
    path('admin-api/presensi/scan', views.admin_scan_presensi, name='admin_scan_presensi_noslash'),
    path('admin-api/presensi/scan/', views.admin_scan_presensi, name='admin_scan_presensi'),
    path('admin-api/presensi/riwayat', views.admin_riwayat_presensi, name='admin_riwayat_presensi_noslash'),
    path('admin-api/presensi/riwayat/', views.admin_riwayat_presensi, name='admin_riwayat_presensi'),
    
    # Admin Endpoint Export Excel Presensi
    path('admin-api/presensi/export-excel/', views.admin_export_presensi_excel, name='admin_export_presensi_excel'),

    # Admin Berita APIs
    path('admin-api/berita/', views.admin_berita_list_create, name='admin_berita_list_create'),
    path('admin-api/berita/<str:pk>/', views.admin_berita_detail, name='admin_berita_detail'),
    
    # Admin Pengumuman APIs
    path('admin-api/pengumuman/', views.admin_pengumuman_list_create, name='admin_pengumuman_list_create'),
    path('admin-api/pengumuman/<str:pk>/', views.admin_pengumuman_detail, name='admin_pengumuman_detail'),
    
    # Admin Guru & SDM APIs
    path('admin-api/guru/', views.admin_guru_list_create, name='admin_guru_list_create'),
    path('admin-api/guru/<int:pk>/', views.admin_guru_detail, name='admin_guru_detail'),

    # Admin Galeri Album APIs (Mendukung upload foto dengan trailing slash fleksibel)
    path('admin-api/galeri/album/', views.admin_album_list_create, name='admin_album_list_create'),
    path('admin-api/galeri/album/<uuid:pk>/', views.admin_album_detail, name='admin_album_detail'),
    path('admin-api/galeri/album/<uuid:album_pk>/upload-foto', views.admin_foto_upload, name='admin_foto_upload_noslash'),
    path('admin-api/galeri/album/<uuid:album_pk>/upload-foto/', views.admin_foto_upload, name='admin_foto_upload'),
    path('admin-api/galeri/foto/<uuid:pk>/', views.admin_foto_delete, name='admin_foto_delete'),

    # Admin Galeri Video APIs
    path('admin-api/galeri/video/', views.admin_video_list_create, name='admin_video_list_create'),
    path('admin-api/galeri/video/<uuid:pk>/', views.admin_video_detail, name='admin_video_detail'),

    # Admin Profil Sekolah API
    path('admin-api/profil/', views.admin_profil_detail_update, name='admin_profil_detail_update'),

    # Admin Hero Banner APIs
    path('admin-api/hero/', views.admin_hero_banner_list_create, name='admin_hero_banner_list_create'),
    path('admin-api/hero/<int:pk>/', views.admin_hero_banner_detail, name='admin_hero_banner_detail'),

    # User Management APIs (Admin)
    path('admin-api/users/', views.admin_user_list_create, name='admin_user_list_create'),
    path('admin-api/users/<int:pk>/', views.admin_user_detail, name='admin_user_detail'),

    # User Directory API (Portal Pengguna)
    path('user-api/users/', views.user_list, name='user_list'),

    # API Autentikasi JWT
    path('auth/login/', views.login_view, name='jwt_login'),
    path('auth/logout/', views.logout_view, name='jwt_logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),
    path('auth/me/', views.me_view, name='auth_me'),

    # API Public Event
    path('event/', views.get_event, name='get_event'),
    path('event/<str:pk>/', views.get_event_detail, name='get_event_detail'),

    # Admin Event APIs
    path('admin-api/event/', views.admin_event_list_create, name='admin_event_list_create'),
    path('admin-api/event/<str:pk>/', views.admin_event_detail, name='admin_event_detail'),

    # API Postingan, Like & Komentar
    path('user-api/posts/', views.user_post_list_create, name='user_post_list_create'),
    path('user-api/posts/me/', views.user_my_posts, name='user_my_posts'),
    path('user-api/posts/<uuid:pk>/like/', views.user_post_like_toggle, name='user_post_like_toggle'),
    path('user-api/posts/<uuid:pk>/comments/', views.user_post_comment_list_create, name='user_post_comment_list_create'),
    path('user-api/posts/<uuid:pk>/', views.user_post_delete, name='user_post_delete'),

    # API Note / Status (12 Jam)
    path('user-api/notes/', views.user_note_list_create, name='user_note_list_create'),
    path('user-api/notes/<uuid:pk>/like/', views.user_note_like_toggle, name='user_note_like_toggle'),
    path('user-api/notes/<uuid:pk>/', views.user_note_delete, name='user_note_delete'),

    # API Download Lampiran Pengumuman
    path('pengumuman/<str:pk>/download/', views.download_pengumuman_lampiran, name='download_pengumuman_lampiran'),
    path('pengumuman/<str:pk>/preview/', views.preview_pengumuman_lampiran, name='preview_pengumuman_lampiran'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)