from os import path, remove

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import TaskAnswer

# https://docs.djangoproject.com/en/3.2/ref/signals/

@receiver(post_delete, sender=TaskAnswer)
def task_answer_delete(sender, instance: TaskAnswer, **kwargs):
    """
    Delete uploaded files from filesystem when corresponding TaskAnswer object is deleted
    """
    if instance.files:
        pass
        #print('signals.py task_answer_delete', instance.files)
        #if os.path.isfile(instance.file.path):
        #    os.remove(instance.file.path)