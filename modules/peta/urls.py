from django.urls import path, include

from . import views
app_name = 'peta'
urlpatterns = [
    path('', views.index, name='peta-index'),
    path('sekolah/', views.sekolah, name='peta-sekolah'),
]