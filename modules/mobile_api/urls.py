from django.urls import path

from modules.mobile_api import views


urlpatterns = [
    path('login', views.LoginSiswaView.as_view(), name='mobile-login'),
    path('login/', views.LoginSiswaView.as_view(), name='mobile-login-slash'),
    path('siswa/profile', views.SiswaProfileView.as_view(), name='mobile-siswa-profile'),
    path('siswa/edit-profile', views.EditProfileView.as_view(), name='mobile-siswa-edit-profile'),
    path('siswa/hb', views.SiswaHbView.as_view(), name='mobile-siswa-hb'),
    path('ttd', views.UploadKonsumsiView.as_view(), name='mobile-ttd'),
    path('riwayat-konsumsi', views.RiwayatKonsumsiView.as_view(), name='mobile-riwayat-konsumsi'),
    path('riwayat-konsumsi/<int:distribusi_id>', views.DetailRiwayatKonsumsiView.as_view(), name='mobile-riwayat-konsumsi-detail'),
    path('sekolah/lokasi', views.SekolahLokasiView.as_view(), name='mobile-sekolah-lokasi'),
]
