from dataclasses import dataclass

from rest_framework import exceptions
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@dataclass
class MobileSiswaUser:
    siswa_id: int
    nis: str
    nama: str
    sekolah_id: int | None = None
    sekolah: str | None = None

    @property
    def is_authenticated(self):
        return True


def get_bearer_payload(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise exceptions.AuthenticationFailed('Token tidak ditemukan')

    try:
        token = AccessToken(parts[1])
    except TokenError:
        raise exceptions.AuthenticationFailed('Token tidak valid')

    payload = token.payload
    if not payload.get('siswa_id') or not payload.get('nis'):
        raise exceptions.AuthenticationFailed('Token tidak valid')

    return payload


def get_mobile_user(request):
    payload = get_bearer_payload(request)
    return MobileSiswaUser(
        siswa_id=payload.get('siswa_id'),
        nis=payload.get('nis'),
        nama=payload.get('nama', ''),
        sekolah_id=payload.get('sekolah_id'),
        sekolah=payload.get('sekolah'),
    )
