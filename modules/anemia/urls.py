from django.urls import path

from modules.anemia import views


app_name = 'anemia'

urlpatterns = [
    path('', views.AnemiaInputView.as_view(), name='input'),
    path('hasil/', views.AnemiaResultView.as_view(), name='result'),
]
