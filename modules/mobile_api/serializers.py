from decimal import Decimal

from rest_framework import serializers


class LoginSiswaSerializer(serializers.Serializer):
    nis = serializers.CharField(required=True, allow_blank=False)
    kode_sekolah = serializers.CharField(required=True, allow_blank=False)


class EditProfileSerializer(serializers.Serializer):
    nama = serializers.CharField(required=True, allow_blank=False)
    email = serializers.EmailField(required=True, allow_blank=False)
    tmp_lahir = serializers.CharField(required=True, allow_blank=False)
    tgl_lahir = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=['L', 'P'])
    tinggi_badan = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))
    berat_badan = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))


class UploadKonsumsiSerializer(serializers.Serializer):
    distribusi_id = serializers.IntegerField(required=True)
    tanggal_konsumsi = serializers.DateField(required=True)
    keterangan = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    file = serializers.ImageField(required=True)

    def validate_file(self, file):
        allowed_extensions = {'jpg', 'jpeg', 'png'}
        extension = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''

        if extension not in allowed_extensions:
            raise serializers.ValidationError('Format file harus JPG, JPEG, atau PNG')

        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Ukuran file maksimal 5MB')

        return file
