
from django.urls import path, include
from . import views

app_name = 'info'
urlpatterns = [
   path('', views.index, name='index' ),
   #path('infopemda', infopemda_views.InfoPemdaView.as_view(), name='infopemda-list' ),
   #path('infopemda/create', infopemda_views.InfoPemdaCreateView.as_view(), name='infopemda-create' ),
   #path('infopemda/delete/<int:pk>', infopemda_views.InfoPemdaDeleteView.as_view(), name='infopemda-delete' ),
   #path('infopemda/edit/<int:pk>', infopemda_views.InfoPemdaUpdateView.as_view(), name='infopemda-edit' ),
]
