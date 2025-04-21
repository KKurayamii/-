from django.apps import AppConfig


class DiabetesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "diabetes"

    def ready(self):
        from .scheduler import start_scheduler
        start_scheduler()
