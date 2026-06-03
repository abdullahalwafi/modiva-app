from django.urls import path, include
from . import views

app_name = 'landingpage'
urlpatterns = [
   path('', views.homepage, name='home' ),
   path('home', views.homepage,  name='home'),
   path('about/', views.about_us, name='about'),
   path('daftar/', views.daftar, name='daftar'),
   path('lupa_password/', views.lupa_password, name='lupa_password'),
   path('password_reset/', views.password_reset, name='password_reset'),
   path('mitra/', views.mitra, name='mitra'),
   path('sk/', views.sk, name='sk'),
   path('privasi/', views.privasi, name='privasi'),
   path('puskesmas/', views.puskesmas, name='puskesmas'),
   path('sekolah/', views.sekolah, name='sekolah'),
   path('profilpuskesmas/<int:pk>', views.profilpuskesmas, name='profilpuskesmas'),
   path('profilsekolah/<int:pk>', views.profilsekolah, name='profilsekolah'),
   #path('daftar/', views.pendaftaran_view, name='contact_form'),
    #path('admin/', admin.site.urls),
   path('pendaftaran-sukses/', views.pendaftaran_sukses, name='pendaftaran_sukses'),
   path('mobile-app/', views.mobile_app, name='mobile_app'),

   path("chat-api", views.chat_api, name="chat_api"),


]
