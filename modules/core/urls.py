
from django.urls import path, include
from . import views, tableu_views
from . import ajaxselect_views

app_name = 'core'
urlpatterns = [
   path('', views.index, name='index' ),
   path('embed', views.EmbedView.as_view(), name='embed'),
   path('tableu', tableu_views.tableu_embed, name='tableu-embed'),
   #path('dashboard', dashboard_views.dashboard, name='dashboard'),
   path('layanan/', views.layanan, name='seluruh-layanan'),
   path('landing_page/', views.landing_page, name='landing-page'),
  
]

handler403 = 'modules.core.views.custom_permission_denied_view'
