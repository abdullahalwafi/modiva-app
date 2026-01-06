from django.apps import AppConfig


class MytaskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.mytask'
    def ready(self):
        import modules.mytask.signals
