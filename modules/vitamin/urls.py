
from django.urls import path, include

from . import provinsi_views,kabkota_views, kecamatan_views, kelurahan_views, puskesmas_views, vitamin_views, satuan_views, sekolah_views, stokobat_views, disobat_views, distsiswa_views, dashboard_views, masterobat_views, formemail_views, siswa_views, siswahb_views

app_name = 'vitamin'
urlpatterns = [
      #-----------provinsi--------------- 
   path('referensi/provinsi', provinsi_views.ProvinsiListView.as_view(), name='provinsi-list'),
   path('referensi/provinsi/create', provinsi_views.ProvinsiCreateView.as_view(), name='provinsi-create'),
   path('referensi/provinsi/edit/<int:pk>', provinsi_views.ProvinsiUpdateView.as_view(), name='provinsi-edit'),
   path('referensi/provinsi/delete/<int:pk>', provinsi_views.ProvinsiDeleteView.as_view(), name='provinsi-delete'),
   path('referensi/provinsi/detail/<int:pk>', provinsi_views.ProvinsiDetailView.as_view(), name='provinsi-detail'),

         #-----------kabkota--------------- 
   path('referensi/kabkota', kabkota_views.KabKotaListView.as_view(), name='kabkota-list'),
   path('referensi/kabkota/create', kabkota_views.KabKotaCreateView.as_view(), name='kabkota-create'),
   path('referensi/kabkota/edit/<int:pk>', kabkota_views.KabKotaUpdateView.as_view(), name='kabkota-edit'),
   path('referensi/kabkota/delete/<int:pk>', kabkota_views.KabKotaDeleteView.as_view(), name='kabkota-delete'),
   path('referensi/kabkota/detail/<int:pk>', kabkota_views.KabKotaDetailView.as_view(), name='kabkota-detail'),

            #-----------kecamatan--------------- 
   path('referensi/kecamatan', kecamatan_views.KecamatanListView.as_view(), name='kecamatan-list'),
   path('referensi/kecamatan/create', kecamatan_views.KecamatanCreateView.as_view(), name='kecamatan-create'),
   path('referensi/kecamatan/edit/<int:pk>', kecamatan_views.KecamatanUpdateView.as_view(), name='kecamatan-edit'),
   path('referensi/kecamatan/delete/<int:pk>', kecamatan_views.KecamatanDeleteView.as_view(), name='kecamatan-delete'),
   path('referensi/kecamatan/detail/<int:pk>', kecamatan_views.KecamatanDetailView.as_view(), name='kecamatan-detail'),

            #-----------kelurahan--------------- 
   path('referensi/kelurahan', kelurahan_views.KelurahanListView.as_view(), name='kelurahan-list'),
   path('referensi/kelurahan/create', kelurahan_views.KelurahanCreateView.as_view(), name='kelurahan-create'),
   path('referensi/kelurahan/edit/<int:pk>', kelurahan_views.KelurahanUpdateView.as_view(), name='kelurahan-edit'),
   path('referensi/kelurahan/delete/<int:pk>', kelurahan_views.KelurahanDeleteView.as_view(), name='kelurahan-delete'),
   path('referensi/kelurahan/detail/<int:pk>', kelurahan_views.KelurahanDetailView.as_view(), name='kelurahan-detail'),

               #-----------puskesmas--------------- 
   path('referensi/puskesmas', puskesmas_views.PuskesmasListView.as_view(), name='puskesmas-list'),
   path('referensi/puskesmas/create', puskesmas_views.PuskesmasCreateView.as_view(), name='puskesmas-create'),
   path('referensi/puskesmas/edit/<int:pk>', puskesmas_views.PuskesmasUpdateView.as_view(), name='puskesmas-edit'),
   path('referensi/puskesmas/delete/<int:pk>', puskesmas_views.PuskesmasDeleteView.as_view(), name='puskesmas-delete'),
   path('referensi/puskesmas/detail/<int:pk>', puskesmas_views.PuskesmasDetailView.as_view(), name='puskesmas-detail'),
   path('referensi/puskesmas/editstatus/<int:pk>', puskesmas_views.PuskesmasUpdateView2.as_view(), name='puskesmas-edit2'),
   path('referensi/puskesmas/toggle-status/<int:pk>/', puskesmas_views.toggle_status_puskesmas, name='toggle_status_puskesmas'),

                  #-----------vitamin--------------- 
   path('referensi/vitamin', vitamin_views.VitaminListView.as_view(), name='vitamin-list'),
   path('referensi/vitamin/create', vitamin_views.VitaminCreateView.as_view(), name='vitamin-create'),
   path('referensi/vitamin/edit/<int:pk>', vitamin_views.VitaminUpdateView.as_view(), name='vitamin-edit'),
   path('referensi/vitamin/delete/<int:pk>', vitamin_views.VitaminDeleteView.as_view(), name='vitamin-delete'),
   path('referensi/vitamin/detail/<int:pk>', vitamin_views.VitaminDetailView.as_view(), name='vitamin-detail'),
   path('download-template-vitamin/', vitamin_views.download_template, name='download_template_ref_vitamin'),
   path('import-excel-vitamin/', vitamin_views.import_excel, name='import_excel_vitamin'),

     #-----------satuan--------------- 
   path('referensi/satuan', satuan_views.SatuanListView.as_view(), name='satuan-list'),
   path('referensi/satuan/create', satuan_views.SatuanCreateView.as_view(), name='satuan-create'),
   path('referensi/satuan/edit/<int:pk>', satuan_views.SatuanUpdateView.as_view(), name='satuan-edit'),
   path('referensi/satuan/delete/<int:pk>', satuan_views.SatuanDeleteView.as_view(), name='satuan-delete'),
   path('referensi/satuan/detail/<int:pk>', satuan_views.SatuanDetailView.as_view(), name='satuan-detail'),
   path('download-template-satuan/', satuan_views.download_template, name='download_template_ref_satuan'),
   path('import-excel-satuan/', satuan_views.import_excel, name='import_excel_satuan'),


                  #-----------sekolah--------------- 
   path('referensi/sekolah', sekolah_views.SekolahListView.as_view(), name='sekolah-list'),
   path('referensi/sekolah/create', sekolah_views.SekolahCreateView.as_view(), name='sekolah-create'),
   path('referensi/sekolah/edit/<int:pk>', sekolah_views.SekolahUpdateView.as_view(), name='sekolah-edit'),
   path('referensi/sekolah/delete/<int:pk>', sekolah_views.SekolahDeleteView.as_view(), name='sekolah-delete'),
   path('referensi/sekolah/detail/<int:pk>', sekolah_views.SekolahDetailView.as_view(), name='sekolah-detail'),
   path('referensi/sekolah/toggle-status/<int:pk>/', sekolah_views.toggle_status_sekolah, name='toggle_status_sekolah'),

      #-----------master_obat--------------- 
   path('masterobat', masterobat_views.MasterObatListView.as_view(), name='masterobat-list'),
   path('masterobat/create', masterobat_views.MasterObatCreateView.as_view(), name='masterobat-create'),
   path('masterobat/edit/<int:pk>', masterobat_views.MasterObatUpdateView.as_view(), name='masterobat-edit'),
   path('masterobat/delete/<int:pk>', masterobat_views.MasterObatDeleteView.as_view(), name='masterobat-delete'),
   path('masterobat/detail/<int:pk>', masterobat_views.MasterObatDetailView.as_view(), name='masterobat-detail'),
   path('download-template-masterobat/', masterobat_views.download_template, name='download_template_masterobat'),
   path('import-excel-masterobat/', masterobat_views.import_excel, name='import_excel_masterobat'),
  
   #-----------stok_obat--------------- 
   path('puskesmas/stokobat', stokobat_views.StokObatListView.as_view(), name='stokobat-list'),
   path('puskesmas/stokobat/create', stokobat_views.StokObatCreateView.as_view(), name='stokobat-create'),
   path('puskesmas/stokobat/edit/<int:pk>', stokobat_views.StokObatUpdateView.as_view(), name='stokobat-edit'),
   path('puskesmas/stokobat/delete/<int:pk>', stokobat_views.StokObatDeleteView.as_view(), name='stokobat-delete'),
   path('puskesmas/stokobat/detail/<int:pk>', stokobat_views.StokObatDetailView.as_view(), name='stokobat-detail'),
   path('download-template-stokobat/', stokobat_views.download_template, name='download_template_stokobat'),
   path('import-excel-stokobat/', stokobat_views.import_excel, name='import_excel_stokobat'),
   path('stokobat/get-isi/', stokobat_views.get_masterobat_isi, name='get-masterobat-isi'),

      #-----------distribusi_obat--------------- 
   path('puskesmas/disobat', disobat_views.DisObatListView.as_view(), name='disobat-list'),
   path('puskesmas/disobat/create', disobat_views.DisObatCreateView.as_view(), name='disobat-create'),
   path('puskesmas/disobat/edit/<int:pk>', disobat_views.DisObatUpdateView.as_view(), name='disobat-edit'),
   path('puskesmas/disobat/delete/<int:pk>', disobat_views.DisObatDeleteView.as_view(), name='disobat-delete'),
   path('puskesmas/disobat/detail/<int:pk>', disobat_views.DisObatDetailView.as_view(), name='disobat-detail'),
   path('download-template-distribusiobat/', disobat_views.download_template, name='download_template_distribusiobat'),
   path('import-excel-distribusiobat/', disobat_views.import_excel, name='import_excel_distribusiobat'),


    #-----------distribusi_siswa--------------- 
   path('sekolah/distsiswa', distsiswa_views.DistSiswaListView.as_view(), name='distsiswa-list'),
   path('sekolah/distsiswa/create', distsiswa_views.DistSiswaCreateView.as_view(), name='distsiswa-create'),
   path('sekolah/distsiswa/edit/<int:pk>', distsiswa_views.DistSiswaUpdateView.as_view(), name='distsiswa-edit'),
   path('sekolah/distsiswa/delete/<int:pk>', distsiswa_views.DistSiswaDeleteView.as_view(), name='distsiswa-delete'),
   path('sekolah/distsiswa/detail/<int:pk>', distsiswa_views.DistSiswaDetailView.as_view(), name='distsiswa-detail'),
   path('download-template-distribusisiswa/', distsiswa_views.download_template, name='download_template_distribusisiswa'),
   path('import-excel-distribusisiswa/', distsiswa_views.import_excel, name='import_excel_distribusisiswa'),

      #-----------form email--------------- 
   path('formemail', formemail_views.ContactMessageListView.as_view(), name='contactmessage-list'),
   path('formemail/edit/<int:pk>', formemail_views.ContactMessageUpdateView.as_view(), name='contactmessage-edit'),
   path('formemail/delete/<int:pk>', formemail_views.ContactMessageDeleteView.as_view(), name='contactmessage-delete'),
   path('formemail/detail/<int:pk>', formemail_views.ContactMessageDetailView.as_view(), name='contactmessage-detail'),



   #-----------Beranda--------------- 
   path('dashboard', dashboard_views.DisObatListView.as_view(), name='dashboard-list'),
   path('dashboard_superadmin_form/', dashboard_views.dashboard_superadmin_form, name='dashboard_superadmin_form'),

   #path('puskesmaslist/<str:pk>/', puskesmas_views.ListPuskesmasByKode, name='puskesmas-detailbykode')
   path('referensi/puskesmas/profilpuskesmas/<int:pk>', puskesmas_views.profilpuskesmas, name='profilpuskesmas'),


                     #-----------siswa--------------- 
   path('sekolah/siswa', siswa_views.SiswaListView.as_view(), name='siswa-list'),
   path('sekolah/siswa/create', siswa_views.SiswaCreateView.as_view(), name='siswa-create'),
   path('sekolah/siswa/edit/<int:pk>', siswa_views.SiswaUpdateView.as_view(), name='siswa-edit'),
   path('sekolah/siswa/delete/<int:pk>', siswa_views.SiswaDeleteView.as_view(), name='siswa-delete'),
   path('sekolah/siswa/detail/<int:pk>', siswa_views.SiswaDetailView.as_view(), name='siswa-detail'),
   path('download-template-siswa/', siswa_views.download_template, name='download_template_siswa'),
   path('import-excel-siswa/', siswa_views.import_excel, name='import_excel_siswa'),

                        #-----------siswa HB--------------- 
   path('sekolah/siswahb', siswahb_views.SiswaHbListView.as_view(), name='siswahb-list'),
   path('sekolah/siswahb/create', siswahb_views.SiswaHbCreateView.as_view(), name='siswahb-create'),
   path('sekolah/siswahb/edit/<int:pk>', siswahb_views.SiswaHbUpdateView.as_view(), name='siswahb-edit'),
   path('sekolah/siswahb/delete/<int:pk>', siswahb_views.SiswaHbDeleteView.as_view(), name='siswahb-delete'),
   path('sekolah/siswahb/detail/<int:pk>', siswahb_views.SiswaHbDetailView.as_view(), name='siswahb-detail'),
   path('download-template-siswahb/', siswahb_views.download_template, name='download_template_siswahb'),
   path('import-excel-siswahb/', siswahb_views.import_excel, name='import_excel_siswahb'),
 
]