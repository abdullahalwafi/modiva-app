import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from importlib import import_module
import inspect
from pathlib import Path
import importlib.util

from django.conf import settings
from django.contrib.admin.options import ModelAdmin
from django.urls import URLResolver, URLPattern


def is_modeladmin_view(view):
    """Return True if the view is an admin view."""
    view = inspect.unwrap(view)  # In case this is a decorated view
    self = getattr(view, "__self__", None)
    return self is not None and isinstance(self, ModelAdmin)


def get_all_views(urlpatterns):
    """Given a URLconf, return a set of all view objects."""
    views = set()
    for pattern in urlpatterns:
        if hasattr(pattern, "url_patterns"):
            views |= get_all_views(pattern.url_patterns)
        else:
            if hasattr(pattern.callback, "cls"):
                view = pattern.callback.cls
            elif hasattr(pattern.callback, "view_class"):
                view = pattern.callback.view_class
            else:
                view = pattern.callback
            if not is_modeladmin_view(view):
                views.add(view)
    return views


def get_module_path(module_name):
    """Return the path for a given module name."""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise ImportError(f"Module '{module_name}' not found")
    return Path(spec.origin).resolve()


def is_subpath(path, directory):
    """Return True if path is below directory and isn't within a "venv"."""
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    else:
        # Return True if view isn't under a directory ending in "venv"
        return not any(p.endswith("venv") for p in path.parts)


def get_all_local_views():
    """Return a set of all local views in this project."""
    root_urlconf = import_module(settings.ROOT_URLCONF)
    all_urlpatterns = root_urlconf.urlpatterns
    try:
        root_directory = settings.ROOT_DIR
    except AttributeError:
        root_directory = Path.cwd()  # Assume we're in the root directory
    return {
        view
        for view in get_all_views(all_urlpatterns)
        if is_subpath(get_module_path(view.__module__), root_directory)
    }


all_views = get_all_local_views()
#print(all_views)
for v in all_views:
   print(v)
print("Number of local views:", len(all_views))
root_urlconf = import_module(settings.ROOT_URLCONF)
all_urlpatterns = root_urlconf.urlpatterns
print(all_urlpatterns)

