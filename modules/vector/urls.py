from django.urls import path
from .views import upload_page, delete_document

app_name = "vector"
urlpatterns = [
    path("", upload_page, name="upload_page"),   
    path("delete/<int:doc_id>/", delete_document, name="delete_document"),     # halaman upload PDeF
]
