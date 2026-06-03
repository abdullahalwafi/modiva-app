"""starter URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path(settings.ROOT_URL + 'xadminx/defender/', include("defender.urls")),
    path(settings.ROOT_URL + 'xadminx/', admin.site.urls),
    path(settings.ROOT_URL + '', include('modules.urls')),
    path(settings.ROOT_URL + 'api/', include('modules.mobile_api.urls')),
    path(settings.ROOT_URL + 'api-auth/', include('rest_framework.urls')),
    path(settings.ROOT_URL + 'xaccountsx/', include('allauth.urls')),
    #path(settings.ROOT_URL + 'accounts/', include('allauth.urls')),
    path(settings.ROOT_URL +'api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path(settings.ROOT_URL +'api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path(settings.ROOT_URL , include('modules.landingpage.urls')),
    path(settings.ROOT_URL + 'vector/' , include('modules.vector.urls', namespace='vector'))
]

if settings.INCLUDE_EXAMPLES:
    urlpatterns += [
        path(settings.ROOT_URL + 'examples/', include('modules.examples.urls')),
    ]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    
else:
    urlpatterns += staticfiles_urlpatterns()
