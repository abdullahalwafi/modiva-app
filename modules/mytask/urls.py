
from django.urls import path, include
from . import views, log_menu_views,produk_views,menuproduk_views ,hasil_kirim_views

app_name = 'mytask'
urlpatterns = [
   #path('', views.index, name='index' ),
   path('log_aktifitas', log_menu_views.LogMenuListView.as_view(), name='log-aktifitas' ),
   path('log_aktifitas/<int:pk>', log_menu_views.LogMenuDetailView.as_view(), name='log-aktifitas-detail' ),
   path('log_aktifitas_kirim/<int:pk>', log_menu_views.DialogKirim, name='log-aktifitas-kirim' ),
   path('produk', produk_views.ProdukListView.as_view(), name='produk-list' ),
   path('produk_add', produk_views.ProdukCreateView.as_view(), name='produk-create' ),
   path('produk_edit/<int:pk>', produk_views.ProdukUpdateView.as_view(), name='produk-edit' ),
   path('produk_detail/<int:pk>', produk_views.ProdukDetailView.as_view(), name='produk-detail' ),
   path('produk_delete/<int:pk>', produk_views.ProdukDeleteView.as_view(), name='produk-delete' ),
   path('menuproduk_add', menuproduk_views.MenuProdukCreateView.as_view(), name='menuproduk-create' ),
   path('menuproduk_edit/<int:pk>', menuproduk_views.MenuProdukUpdateView.as_view(), name='menuproduk-edit' ),
   path('hasil_kirim', hasil_kirim_views.HasilKirimListView.as_view(), name='hasil-kirim-list' ),
]
