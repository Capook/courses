from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

# copied from users config from the initial setup with cookiecutter.  the app is named courses.selfgrade


class SelfgradeConfig(AppConfig):
    name = "courses.selfgrade"
    verbose_name = _("Selfgrade")

    def ready(self):
        import courses.selfgrade.signals
