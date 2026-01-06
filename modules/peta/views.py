from django.shortcuts import render
from modules.vitamin.models import Puskesmas,KabKota,Kecamatan,Kelurahan,Sekolah
import json

def index(request):
    puskesmas_list = list(Puskesmas.objects.values('kode','nama', 'gps_koordinat','kelurahan__nama','kelurahan__kecamatan__nama'))
    return render(request, 'peta/index.html',{
        'puskesmas_json': json.dumps(puskesmas_list)
    })
    #return render(request, 'uman/login.html')

def sekolah(request):
    user = request.user if request.user.is_authenticated else None
    user_kecamatan = None

    # Jika user login, tentukan kecamatannya (role puskesmas / kecamatan)
    if user and hasattr(user, 'puskesmas'):
        user_kecamatan = user.puskesmas.kelurahan.kecamatan
    elif user and hasattr(user, 'kecamatan'):
        user_kecamatan = user.kecamatan

    # Ambil semua sekolah yang memiliki koordinat
    sekolah_qs = Sekolah.objects.filter(gps_koordinat__isnull=False).exclude(gps_koordinat='')

    # Jika login, tetap tampilkan semua data, tapi tandai kecamatan user untuk auto-select
    sekolah_list = list(
        sekolah_qs.values(
            'kode',
            'nama',
            'gps_koordinat',
            'kelurahan__nama',
            'kelurahan__kecamatan__nama',
            'kelurahan__kecamatan__id'
        )
    )

    # Ambil daftar kecamatan untuk filter dropdown
    kecamatan_qs = Kecamatan.objects.values('id', 'nama').order_by('nama')
    kecamatan_list = list(kecamatan_qs)

    return render(request, 'peta/sekolah.html', {
        'sekolah_json': json.dumps(sekolah_list),
        'kecamatan_list': kecamatan_list,
        'selected_kecamatan_id': user_kecamatan.id if user_kecamatan else '',
    })