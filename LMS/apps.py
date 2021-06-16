from django.apps import AppConfig

class LmsConfig(AppConfig):
    name = 'LMS'

    # Django start two processes, one for the actual development server
    # and other to reload your application when the code change.

    # отключить перезагрузку при изменении кода
    # python manage.py runserver --noreload

    # run code when Django starts
    def ready(self):
        import LMS.signals

        from .celery_tasks import check_files
        print('ready')
        check_files.delay() # .run ?