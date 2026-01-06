from django.apps import AppConfig


class UmanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.uman'
    def ready(self):
        import modules.uman.signals

