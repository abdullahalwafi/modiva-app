from django.urls import path, include

urlpatterns = [
    path('', include('modules.uman.urls')),
    path('core/',include('modules.core.urls')),
    path('mytask/',include('modules.mytask.urls')),
    path('info/',include('modules.info.urls')),
    path('vitamin/',include('modules.vitamin.urls')),
    path('landingpage/',include('modules.landingpage.urls')),
    path('peta/',include('modules.peta.urls',namespace='peta')),
    path('vector/',include('modules.vector.urls',namespace='vector')),
    #path('logviewer/', include('logviewer.urls', namespace='logviewer')),
    #path("__debug__/", include("debug_toolbar.urls")),

]
