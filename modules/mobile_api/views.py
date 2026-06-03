import os
from decimal import Decimal

from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

from modules.mobile_api.authentication import get_mobile_user
from modules.mobile_api.serializers import (
    EditProfileSerializer,
    LoginSiswaSerializer,
    UploadKonsumsiSerializer,
)
from modules.vitamin.models import Distribusisiswa, Sekolah, Siswa, SiswaHB


def decimal_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def serialize_siswa(siswa):
    return {
        'siswa_id': siswa.id,
        'nis': siswa.nis,
        'nama': siswa.nama,
        'email': siswa.email,
        'tmp_lahir': siswa.tmp_lahir,
        'tgl_lahir': siswa.tgl_lahir.isoformat() if siswa.tgl_lahir else None,
        'gender': siswa.gender,
        'tinggi_badan': decimal_to_float(siswa.tinggi_badan),
        'berat_badan': decimal_to_float(siswa.berat_badan),
        'sekolah': siswa.sekolah.nama,
        'sekolah_id': siswa.sekolah_id,
    }


def serialize_distribusi(item, request=None):
    bukti_foto = item.bukti_foto.url if item.bukti_foto else None
    if bukti_foto and request is not None:
        bukti_foto = request.build_absolute_uri(bukti_foto)

    return {
        'id': item.id,
        'nis': item.nis,
        'nama_siswa': item.nama_siswa,
        'tgl_terima': item.tgl_terima.isoformat() if item.tgl_terima else None,
        'tanggal_konsumsi': item.tanggal_konsumsi.isoformat() if item.tanggal_konsumsi else None,
        'jumlah': item.jumlah,
        'status_konsumsi': item.status_konsumsi,
        'bukti_foto': bukti_foto,
        'keterangan': item.keterangan,
    }


class LoginSiswaView(APIView):
    authentication_classes = []
    permission_classes = []
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        serializer = LoginSiswaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        siswa = (
            Siswa.objects.select_related('sekolah')
            .filter(
                nis=serializer.validated_data['nis'],
                sekolah__kode=serializer.validated_data['kode_sekolah'],
            )
            .first()
        )

        if not siswa:
            return Response({'error': 'NIS atau kode sekolah salah'}, status=status.HTTP_401_UNAUTHORIZED)

        token = AccessToken()
        token['siswa_id'] = siswa.id
        token['nis'] = siswa.nis
        token['nama'] = siswa.nama
        token['sekolah_id'] = siswa.sekolah_id
        token['sekolah'] = siswa.sekolah.nama

        return Response({
            'message': 'Login berhasil',
            'access': str(token),
            'data': {
                'siswa_id': siswa.id,
                'nis': siswa.nis,
                'nama': siswa.nama,
                'sekolah': siswa.sekolah.nama,
            },
        })


class SiswaProfileView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = get_mobile_user(request)
        siswa = Siswa.objects.select_related('sekolah').filter(id=user.siswa_id, nis=user.nis).first()

        if not siswa:
            return Response({'detail': 'Data siswa tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'message': 'Data profil berhasil diambil',
            'data': serialize_siswa(siswa),
        })


class EditProfileView(APIView):
    authentication_classes = []
    permission_classes = []
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def put(self, request):
        user = get_mobile_user(request)
        siswa = Siswa.objects.filter(id=user.siswa_id, nis=user.nis).first()

        if not siswa:
            return Response({'detail': 'Data siswa tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(siswa, field, value)
        siswa.save(update_fields=[
            'nama',
            'email',
            'tmp_lahir',
            'tgl_lahir',
            'gender',
            'tinggi_badan',
            'berat_badan',
            'updated_at',
        ])

        return Response({'message': 'Profil berhasil diperbarui'})


class SiswaHbView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = get_mobile_user(request)
        rows = SiswaHB.objects.filter(siswa_id=user.siswa_id).order_by('tahun')

        data = [
            {
                'tahun': row.tahun,
                'hb': float(row.hb) if row.hb is not None else None,
                'keterangan': row.keterangan,
            }
            for row in rows
        ]

        return Response({
            'message': 'Data HB berhasil diambil',
            'data': data,
        })


class UploadKonsumsiView(APIView):
    authentication_classes = []
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = get_mobile_user(request)
        serializer = UploadKonsumsiSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        distribusi = Distribusisiswa.objects.filter(
            id=serializer.validated_data['distribusi_id'],
            siswa_id=user.siswa_id,
            nis=user.nis,
        ).first()

        if not distribusi:
            return Response({'detail': 'Data distribusi tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)

        file = serializer.validated_data['file']
        tanggal = serializer.validated_data['tanggal_konsumsi']
        extension = file.name.rsplit('.', 1)[-1].lower()
        nama_clean = get_valid_filename((user.nama or distribusi.nama_siswa or 'siswa').replace(' ', '_'))
        filename = f'{user.nis}_{tanggal.strftime("%Y%m%d")}_{nama_clean}.{extension}'
        path = os.path.join('uploads', 'bukti_konsumsi', filename)

        saved_path = default_storage.save(path, file)

        distribusi.tanggal_konsumsi = tanggal
        distribusi.bukti_foto = saved_path
        distribusi.keterangan = serializer.validated_data.get('keterangan') or ''
        distribusi.status_konsumsi = 'sudah'
        distribusi.save(update_fields=[
            'tanggal_konsumsi',
            'bukti_foto',
            'keterangan',
            'status_konsumsi',
            'updated_at',
        ])

        return Response({
            'message': 'Laporan konsumsi berhasil disimpan',
            'file': filename,
            'path': saved_path,
        })


class RiwayatKonsumsiView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = get_mobile_user(request)
        rows = Distribusisiswa.objects.filter(siswa_id=user.siswa_id, nis=user.nis).order_by('-tgl_terima', '-id')
        data = [serialize_distribusi(row, request) for row in rows]

        return Response({
            'message': 'Riwayat konsumsi berhasil diambil',
            'total': len(data),
            'data': data,
        })


class DetailRiwayatKonsumsiView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, distribusi_id):
        user = get_mobile_user(request)
        distribusi = Distribusisiswa.objects.filter(
            id=distribusi_id,
            siswa_id=user.siswa_id,
            nis=user.nis,
        ).first()

        if not distribusi:
            return Response({'detail': 'Riwayat tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'message': 'Detail riwayat berhasil diambil',
            'data': serialize_distribusi(distribusi, request),
        })


class SekolahLokasiView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = get_mobile_user(request)
        sekolah = Sekolah.objects.filter(siswa__id=user.siswa_id).first()

        if not sekolah:
            return Response({'detail': 'Data sekolah tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'nama_sekolah': sekolah.nama,
            'alamat': sekolah.alamat,
            'gps_koordinat': sekolah.gps_koordinat,
        })
