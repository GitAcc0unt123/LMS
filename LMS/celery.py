# файл настроек Celery

import os
from celery import Celery
#from celery.schedules import crontab
 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
 
app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
 
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# см. другой способ задать расписание в settings.py с помощью CELERY_BEAT_SCHEDULE
#app.conf.beat_schedule = {
#   'send-notifications-every-minute': {
#    'task': 'LMS.celery_tasks.sendNotifications',
#    'schedule': crontab(minute='*/1'), # кажд. минуту
#   },
#}

# Linux
# install redis
# https://redis.io/topics/quickstart

# 1. запуск redis
# консоль 1> redis-server
# если порт занят, то sudo service redis-server stop

# 2. запуск django приложения
# (env38_64) консоль 2> python manage.py runserver

# 3. запуск рабочих процессов celery
# (env38_64) консоль 3> celery -A project worker -l info --concurrency=2
# здесь -l info  ==  --loglevel=info - будет писать логи в консоль

# 4. запуск планировщика для выполнения задач по расписанию
# задания выполняются запущенными рабочими процессами
# (env38_64) консоль 4> celery -A project beat -l info

# запуск flower для отображения инфы о работе celery
