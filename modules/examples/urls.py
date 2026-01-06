# Template Example
from os import listdir
from django.urls import path
from django.conf import settings
from django.views.generic.base import TemplateView 
from .views import dashboard_views,account_views,main_views

template_example_widgets = [
    path(f'widgets/{filename.replace(".html", "")}', TemplateView.as_view(template_name=f"examples/widgets/{filename}"))
    for filename in listdir(settings.BASE_DIR / 'templates' / 'examples' / 'widgets')
    if '.html' in filename
]

urlpatterns = [
    # path('', TemplateView.as_view(template_name="examples/index.html")),
    path('', main_views.index_examples),
    path('documentation/', main_views.documentation),
    path('documentation/<path:path>', main_views.index_documentation),
    *account_views.urlpatterns,
    *dashboard_views.urlpatterns,
    *template_example_widgets,
]

