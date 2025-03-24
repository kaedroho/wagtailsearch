from django.apps import AppConfig


class TestAppConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "modelsearch.test.testapp"
    label = "searchtests"
    verbose_name = "Test models"
