import random
import re
import secrets
import string
from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Guru, Berita, Pengumuman, Presensi, ProfilSekolah, 
    HeroBanner, AlbumGaleri, UserProfile, VideoGaleri, FotoAlbum, Event,
    Post, PostLike, PostComment, Note, NoteLike
)

# Definisi path avatar default
DEFAULT_AVATAR_PATH = '/media/default-profile/profile-picture.png'


def generate_username_from_name(nama):
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', nama.lower())
    if not clean_name:
        clean_name = "sdm"
    
    base_username = clean_name
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    return username


def generate_secure_default_password(length=12):
    """Menghasilkan password acak yang kuat untuk pengguna baru."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class UserProfileSerializer(serializers.ModelSerializer):
    foto_profil = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['foto_profil', 'motto', 'role_type', 'uuid_code']

    def get_foto_profil(self, obj):
        request = self.context.get('request')
        if obj.foto_profil and hasattr(obj.foto_profil, 'url'):
            foto_url = obj.foto_profil.url
        else:
            foto_url = DEFAULT_AVATAR_PATH

        if request is not None:
            return request.build_absolute_uri(foto_url)
        return foto_url


class GuruSerializer(serializers.ModelSerializer):
    badgeColor = serializers.CharField(source='badge_color', required=False, allow_blank=True)
    foto = serializers.SerializerMethodField()

    class Meta:
        model = Guru
        fields = [
            'id', 'user', 'nama', 'nip', 'jabatan', 'kategori', 'mapel', 
            'motto', 'foto', 'role', 'badgeColor', 'badge_color', 'gelar', 
            'pendidikan_terakhir', 'asal_kampus'
        ]
        extra_kwargs = {
            'badge_color': {'required': False},
            'user': {'read_only': True}
        }

    def get_foto(self, obj):
        request = self.context.get('request')
        if obj.foto and hasattr(obj.foto, 'url'):
            foto_url = obj.foto.url
        else:
            foto_url = DEFAULT_AVATAR_PATH

        if request is not None:
            return request.build_absolute_uri(foto_url)
        return foto_url

    def create(self, validated_data):
        guru = super().create(validated_data)

        if not guru.user:
            username_default = generate_username_from_name(guru.nama)
            password_default = guru.nip if (guru.nip and len(guru.nip) >= 6) else generate_secure_default_password()

            names = guru.nama.strip().split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''

            user = User.objects.create_user(
                username=username_default,
                password=password_default,
                first_name=first_name,
                last_name=last_name
            )
            guru.user = user
            guru.save()

            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            user_profile.role_type = 'staf' if 'staf' in guru.kategori.lower() or 'tu' in guru.kategori.lower() else 'guru'
            if guru.motto:
                user_profile.motto = guru.motto
            if guru.foto:
                user_profile.foto_profil = guru.foto
            user_profile.save()

        return guru

    def update(self, instance, validated_data):
        guru = super().update(instance, validated_data)

        if guru.user:
            user_profile, _ = UserProfile.objects.get_or_create(user=guru.user)
            if 'motto' in validated_data:
                user_profile.motto = guru.motto
            if 'foto' in validated_data and guru.foto:
                user_profile.foto_profil = guru.foto
            user_profile.save()

        return guru


def safe_get_guru(obj):
    try:
        return getattr(obj, 'guru_profile', None)
    except Exception:
        return None

def safe_get_profil(obj):
    try:
        return getattr(obj, 'profil', None)
    except Exception:
        return None


class UserSerializer(serializers.ModelSerializer):
    guru_profile = GuruSerializer(read_only=True)
    profil = UserProfileSerializer(read_only=True)
    motto = serializers.CharField(write_only=True, required=False, allow_blank=True)
    nama_lengkap = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=6)
    foto_profil = serializers.ImageField(write_only=True, required=False, allow_null=True)
    role_type = serializers.CharField(write_only=True, required=False, allow_blank=True)
    roles = serializers.SerializerMethodField()
    qr_uuid = serializers.SerializerMethodField()
    nama = serializers.SerializerMethodField()
    foto = serializers.SerializerMethodField()
    jabatan = serializers.SerializerMethodField()
    nip = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'is_staff', 'is_active', 'guru_profile', 'profil', 'password',
            'motto', 'nama_lengkap', 'foto_profil', 'role_type', 'roles',
            'qr_uuid', 'nama', 'foto', 'jabatan', 'nip'
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': False, 'allow_blank': True}
        }

    def get_roles(self, obj):
        roles_list = []
        if obj.is_staff or obj.is_superuser:
            roles_list.append('admin')

        secondary_role = 'guru'
        if hasattr(obj, 'guru_profile') and obj.guru_profile:
            kat = (obj.guru_profile.kategori or '').lower()
            secondary_role = 'staf' if 'staf' in kat or 'tu' in kat else 'guru'
        elif hasattr(obj, 'profil') and obj.profil and obj.profil.role_type:
            secondary_role = obj.profil.role_type

        if secondary_role not in roles_list:
            roles_list.append(secondary_role)

        return roles_list

    def get_qr_uuid(self, obj):
        profil = safe_get_profil(obj)
        if not profil:
            profil, _ = UserProfile.objects.get_or_create(user=obj)

        if not profil.uuid_code:
            while True:
                random_code = str(random.randint(100000, 999999))
                if not UserProfile.objects.filter(uuid_code=random_code).exists():
                    profil.uuid_code = random_code
                    profil.save(update_fields=['uuid_code'])
                    break

        return profil.uuid_code

    def get_nama(self, obj):
        guru = safe_get_guru(obj)
        if guru and guru.nama:
            return guru.nama
        full_name = obj.get_full_name()
        if full_name and full_name.strip():
            return full_name
        return obj.username

    def get_foto(self, obj):
        request = self.context.get('request')
        foto_url = None

        profil_obj = safe_get_profil(obj)
        guru_obj = safe_get_guru(obj)

        if profil_obj and profil_obj.foto_profil:
            foto_url = profil_obj.foto_profil.url
        elif guru_obj and guru_obj.foto:
            foto_url = guru_obj.foto.url

        if not foto_url:
            foto_url = DEFAULT_AVATAR_PATH

        if request is not None:
            return request.build_absolute_uri(foto_url)
        return foto_url

    def get_jabatan(self, obj):
        guru = safe_get_guru(obj)
        if guru and guru.jabatan:
            return guru.jabatan
        if obj.is_staff or obj.is_superuser:
            return "Administrator Sekolah"
        return "Pengguna SD YWKA"

    def get_nip(self, obj):
        guru = safe_get_guru(obj)
        if guru and guru.nip:
            return guru.nip
        return "-"

    def to_internal_value(self, data):
        if hasattr(data, '_mutable'):
            data = data.copy()
        
        if 'is_staff' in data:
            val = data['is_staff']
            if isinstance(val, str):
                data['is_staff'] = val.lower() in ('true', '1', 't')
        if 'is_active' in data:
            val = data['is_active']
            if isinstance(val, str):
                data['is_active'] = val.lower() in ('true', '1', 't')

        return super().to_internal_value(data)

    def create(self, validated_data):
        motto = validated_data.pop('motto', '')
        nama_lengkap = validated_data.pop('nama_lengkap', '')
        password = validated_data.pop('password', None)
        foto_profil = validated_data.pop('foto_profil', None)
        role_type = validated_data.pop('role_type', 'guru')

        if nama_lengkap:
            names = nama_lengkap.strip().split(' ', 1)
            validated_data['first_name'] = names[0]
            if len(names) > 1:
                validated_data['last_name'] = names[1]

        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_password(generate_secure_default_password())
        user.save()

        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        user_profile.role_type = role_type or 'guru'
        if motto:
            user_profile.motto = motto
        if foto_profil:
            user_profile.foto_profil = foto_profil
        user_profile.save()

        return user

    def update(self, instance, validated_data):
        motto = validated_data.pop('motto', None)
        nama_lengkap = validated_data.pop('nama_lengkap', None)
        password = validated_data.pop('password', None)
        foto_profil = validated_data.pop('foto_profil', None)
        role_type = validated_data.pop('role_type', None)

        if nama_lengkap is not None:
            names = nama_lengkap.strip().split(' ', 1)
            instance.first_name = names[0]
            instance.last_name = names[1] if len(names) > 1 else ''

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        
        instance.save()

        user_profile, _ = UserProfile.objects.get_or_create(user=instance)
        if role_type:
            user_profile.role_type = role_type
        if motto is not None:
            user_profile.motto = motto
        if foto_profil:
            user_profile.foto_profil = foto_profil
        user_profile.save()

        if hasattr(instance, 'guru_profile') and instance.guru_profile:
            guru = instance.guru_profile
            if motto is not None:
                guru.motto = motto
            if nama_lengkap is not None:
                guru.nama = nama_lengkap
            if foto_profil:
                guru.foto = foto_profil
            guru.save()

        return instance


class UserDirectorySerializer(serializers.ModelSerializer):
    nama = serializers.SerializerMethodField()
    quotes = serializers.SerializerMethodField()
    foto = serializers.SerializerMethodField()
    jabatan = serializers.SerializerMethodField()
    kategori = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'nama', 'quotes', 'foto', 'jabatan', 'kategori']

    def get_nama(self, obj):
        full_name = obj.get_full_name()
        if full_name and full_name.strip():
            return full_name
        if hasattr(obj, 'guru_profile') and obj.guru_profile and obj.guru_profile.nama:
            return obj.guru_profile.nama
        return obj.username

    def get_quotes(self, obj):
        if hasattr(obj, 'profil') and obj.profil and obj.profil.motto:
            return obj.profil.motto
        if hasattr(obj, 'guru_profile') and obj.guru_profile and obj.guru_profile.motto:
            return obj.guru_profile.motto
        return "Belum ada bio/quotes"

    def get_foto(self, obj):
        request = self.context.get('request')
        foto_url = None

        if hasattr(obj, 'profil') and obj.profil and obj.profil.foto_profil:
            foto_url = obj.profil.foto_profil.url
        elif hasattr(obj, 'guru_profile') and obj.guru_profile and obj.guru_profile.foto:
            foto_url = obj.guru_profile.foto.url

        if not foto_url:
            foto_url = DEFAULT_AVATAR_PATH

        if request is not None:
            return request.build_absolute_uri(foto_url)
        return foto_url

    def get_jabatan(self, obj):
        if hasattr(obj, 'guru_profile') and obj.guru_profile and obj.guru_profile.jabatan:
            return obj.guru_profile.jabatan
        return "Pengguna SD YWKA"

    def get_kategori(self, obj):
        if hasattr(obj, 'guru_profile') and obj.guru_profile and obj.guru_profile.kategori:
            return obj.guru_profile.kategori
        return "Pengguna"


class BeritaSerializer(serializers.ModelSerializer):
    penulis_nama = serializers.SerializerMethodField()
    penulis_foto = serializers.SerializerMethodField()

    class Meta:
        model = Berita
        fields = '__all__'

    def get_penulis_nama(self, obj):
        if not obj.penulis:
            return "Humas SD YWKA"
        if hasattr(obj.penulis, 'guru_profile') and obj.penulis.guru_profile and obj.penulis.guru_profile.nama:
            return obj.penulis.guru_profile.nama
        full_name = obj.penulis.get_full_name()
        if full_name:
            return full_name
        return obj.penulis.username

    def get_penulis_foto(self, obj):
        if not obj.penulis:
            return None
        request = self.context.get('request')
        foto_url = None

        profil_obj = getattr(obj.penulis, 'profil', None)
        guru_obj = getattr(obj.penulis, 'guru_profile', None)

        if profil_obj and profil_obj.foto_profil:
            foto_url = profil_obj.foto_profil.url
        elif guru_obj and guru_obj.foto:
            foto_url = guru_obj.foto.url

        if not foto_url:
            foto_url = DEFAULT_AVATAR_PATH

        if request is not None:
            return request.build_absolute_uri(foto_url)
        return foto_url


class PengumumanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pengumuman
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.lampiran and hasattr(instance.lampiran, 'url'):
            lampiran_url = instance.lampiran.url
            if request is not None:
                representation['lampiran'] = request.build_absolute_uri(lampiran_url)
            else:
                representation['lampiran'] = lampiran_url
        else:
            representation['lampiran'] = None
        return representation


class ProfilSekolahSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilSekolah
        fields = '__all__'


class HeroBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroBanner
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.gambar and hasattr(instance.gambar, 'url'):
            gambar_url = instance.gambar.url
            if request is not None:
                representation['gambar'] = request.build_absolute_uri(gambar_url)
            else:
                representation['gambar'] = gambar_url
        else:
            representation['gambar'] = None
        return representation


# FIX PERBAIKAN: FotoAlbumSerializer mendukung Upload Gambar & Memberikan Absolute URI
class FotoAlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoAlbum
        fields = ['id', 'album', 'gambar', 'keterangan']
        extra_kwargs = {
            'album': {'required': False, 'read_only': True},
            'gambar': {'required': False, 'allow_null': True}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.gambar and hasattr(instance.gambar, 'url'):
            foto_url = instance.gambar.url
            if request is not None:
                representation['gambar'] = request.build_absolute_uri(foto_url)
            else:
                representation['gambar'] = foto_url
        else:
            representation['gambar'] = None
        return representation


# FIX PERBAIKAN: AlbumGaleriSerializer mendukung Cover File Upload & Output Absolute URI
class AlbumGaleriSerializer(serializers.ModelSerializer):
    fotos = FotoAlbumSerializer(many=True, read_only=True)
    jumlah_foto = serializers.SerializerMethodField()

    class Meta:
        model = AlbumGaleri
        fields = ['id', 'judul', 'kategori', 'tanggal', 'cover', 'deskripsi', 'fotos', 'jumlah_foto', 'tanggal_upload']
        extra_kwargs = {
            'cover': {'required': False, 'allow_null': True}
        }

    def get_jumlah_foto(self, obj):
        return obj.fotos.count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.cover and hasattr(instance.cover, 'url'):
            cover_url = instance.cover.url
            if request is not None:
                representation['cover'] = request.build_absolute_uri(cover_url)
            else:
                representation['cover'] = cover_url
        else:
            representation['cover'] = None
        return representation


class VideoGaleriSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoGaleri
        fields = '__all__'


class UserMeSerializer(serializers.ModelSerializer):
    nama = serializers.SerializerMethodField()
    nama_lengkap = serializers.SerializerMethodField()
    quotes = serializers.SerializerMethodField()
    foto = serializers.SerializerMethodField()
    qr_uuid = serializers.SerializerMethodField()
    uuid_short = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'nama', 'nama_lengkap', 'quotes', 'foto', 'qr_uuid', 'uuid_short', 'roles']

    def get_nama(self, obj):
        guru = safe_get_guru(obj)
        if guru and guru.nama:
            return guru.nama
        full_name = obj.get_full_name()
        if full_name and full_name.strip():
            return full_name
        return obj.username

    def get_nama_lengkap(self, obj):
        return self.get_nama(obj)

    def get_roles(self, obj):
        roles_list = []
        if obj.is_staff or obj.is_superuser:
            roles_list.append('admin')

        secondary_role = 'guru'
        if hasattr(obj, 'guru_profile') and obj.guru_profile:
            kat = (obj.guru_profile.kategori or '').lower()
            secondary_role = 'staf' if 'staf' in kat or 'tu' in kat else 'guru'
        elif hasattr(obj, 'profil') and obj.profil and obj.profil.role_type:
            secondary_role = obj.profil.role_type

        if secondary_role not in roles_list:
            roles_list.append(secondary_role)

        return roles_list

    def get_quotes(self, obj):
        profil = safe_get_profil(obj)
        if profil and profil.motto:
            return profil.motto
        guru = safe_get_guru(obj)
        if guru and guru.motto:
            return guru.motto
        return "Bismillah"

    def get_foto(self, obj):
        request = self.context.get('request')
        foto_url = None

        profil_obj = safe_get_profil(obj)
        guru_obj = safe_get_guru(obj)

        if profil_obj and profil_obj.foto_profil:
            foto_url = profil_obj.foto_profil.url
        elif guru_obj and guru_obj.foto:
            foto_url = guru_obj.foto.url

        if not foto_url:
            foto_url = DEFAULT_AVATAR_PATH

        if request is not None:
            return request.build_absolute_uri(foto_url)
        return foto_url

    def get_uuid_short(self, obj):
        profil = safe_get_profil(obj)
        if not profil:
            profil, _ = UserProfile.objects.get_or_create(user=obj)

        if not profil.uuid_code:
            while True:
                random_code = str(random.randint(100000, 999999))
                if not UserProfile.objects.filter(uuid_code=random_code).exists():
                    profil.uuid_code = random_code
                    profil.save(update_fields=['uuid_code'])
                    break

        return profil.uuid_code

    def get_qr_uuid(self, obj):
        return self.get_uuid_short(obj)


class PresensiSerializer(serializers.ModelSerializer):
    nama_pengguna = serializers.SerializerMethodField()
    sub_info = serializers.SerializerMethodField()
    tanggal_formatted = serializers.SerializerMethodField()
    waktu_formatted = serializers.SerializerMethodField()
    waktu_pulang_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Presensi
        fields = [
            'id', 'user', 'nama_pengguna', 'sub_info', 
            'waktu_scan', 'tanggal_formatted', 'waktu_formatted', 
            'waktu_pulang', 'waktu_pulang_formatted', 
            'status', 'peran'
        ]

    def get_nama_pengguna(self, obj):
        guru = safe_get_guru(obj.user)
        if guru and guru.nama:
            return guru.nama
        return obj.user.get_full_name() or obj.user.username

    def get_sub_info(self, obj):
        guru = safe_get_guru(obj.user)
        if guru and guru.jabatan:
            return guru.jabatan
        return f"Pengguna ID: {obj.user.username}"

    def get_tanggal_formatted(self, obj):
        local_time = timezone.localtime(obj.waktu_scan)
        return local_time.strftime('%d-%m-%Y')

    def get_waktu_formatted(self, obj):
        local_time = timezone.localtime(obj.waktu_scan)
        return local_time.strftime('%H:%M:%S WIB')

    def get_waktu_pulang_formatted(self, obj):
        if obj.waktu_pulang:
            local_time = timezone.localtime(obj.waktu_pulang)
            return local_time.strftime('%H:%M:%S WIB')
        return "-"


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class PostCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_nama = serializers.SerializerMethodField()
    user_foto = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ['id', 'post', 'user', 'username', 'user_nama', 'user_foto', 'teks', 'created_at']
        read_only_fields = ['id', 'user', 'post', 'created_at']

    def get_user_nama(self, obj):
        guru = safe_get_guru(obj.user)
        if guru and guru.nama:
            return guru.nama
        return obj.user.get_full_name() or obj.user.username

    def get_user_foto(self, obj):
        request = self.context.get('request')
        foto_url = None

        profil_obj = safe_get_profil(obj.user)
        guru_obj = safe_get_guru(obj.user)

        if profil_obj and profil_obj.foto_profil:
            foto_url = profil_obj.foto_profil.url
        elif guru_obj and guru_obj.foto:
            foto_url = guru_obj.foto.url

        if not foto_url:
            foto_url = DEFAULT_AVATAR_PATH

        if request is not None:
            return request.build_absolute_uri(foto_url)
        return foto_url


class PostSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_nama = serializers.SerializerMethodField()
    user_foto = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments = PostCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'user_username', 'user_nama', 'user_foto', 
            'gambar', 'caption', 'likes_count', 'comments_count', 
            'is_liked', 'comments', 'tanggal_upload'
        ]
        read_only_fields = ['id', 'user', 'tanggal_upload']

    def get_user_nama(self, obj):
        guru = safe_get_guru(obj.user)
        if guru and guru.nama:
            return guru.nama
        return obj.user.get_full_name() or obj.user.username

    def get_user_foto(self, obj):
        request = self.context.get('request')
        foto_url = None

        profil_obj = safe_get_profil(obj.user)
        guru_obj = safe_get_guru(obj.user)

        if profil_obj and profil_obj.foto_profil:
            foto_url = profil_obj.foto_profil.url
        elif guru_obj and guru_obj.foto:
            foto_url = guru_obj.foto.url

        if not foto_url:
            foto_url = DEFAULT_AVATAR_PATH

        if request is not None:
            return request.build_absolute_uri(foto_url)
        return foto_url

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class NoteSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_nama = serializers.SerializerMethodField()
    user_foto = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    waktu = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ['id', 'user', 'username', 'user_nama', 'user_foto', 'teks', 'likes_count', 'is_liked', 'waktu', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_user_nama(self, obj):
        guru = safe_get_guru(obj.user)
        if guru and guru.nama:
            return guru.nama
        return obj.user.get_full_name() or obj.user.username

    def get_user_foto(self, obj):
        request = self.context.get('request')
        foto_url = None
        profil_obj = safe_get_profil(obj.user)
        guru_obj = safe_get_guru(obj.user)

        if profil_obj and profil_obj.foto_profil:
            foto_url = profil_obj.foto_profil.url
        elif guru_obj and guru_obj.foto:
            foto_url = guru_obj.foto.url

        if not foto_url:
            foto_url = DEFAULT_AVATAR_PATH

        if request is not None:
            return request.build_absolute_uri(foto_url)
        return foto_url

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_waktu(self, obj):
        diff = timezone.now() - obj.created_at
        if diff.days > 0:
            return f"{diff.days} hari yang lalu"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} jam yang lalu"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes} menit yang lalu"
        return "Baru saja"