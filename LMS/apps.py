from django.apps import AppConfig

class LmsConfig(AppConfig):
    name = 'LMS'

    # run code when Django starts
    def ready(self):
        import LMS.signals