from django.urls import path
from modules.mdm import views_mdm

app_name = 'mdm'

urlpatterns = [
    path('', views_mdm.index, name='index'),
    path('master', views_mdm.PreviewMdmView.as_view(), name='master_referensi'),
    path('master/<str:mdm_table_name>/',  views_mdm.PreviewMdmRecordsView.as_view(), name='table_records'),
    path('master/<str:mdm_table_name>/api/', views_mdm.get_table_list, name='master_list_api'),
    path('master-api', views_mdm.PreviewMdmAPIView.as_view(), name='master_api_referensi'),
    path('download-template/<str:mdm_table_name>/', views_mdm.download_template, name='download_template'),


]
