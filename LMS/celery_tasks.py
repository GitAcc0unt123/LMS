# задания для celery

import logging
from datetime import timedelta
from os import path, listdir, rename

from django.conf import settings
from .models import Comment, FileStorage, Notification, TaskAnswer, TaskTestExecution
from .celery import app

logger = logging.getLogger(__name__)


@app.task
def check_files() -> None:
    """"""
    #
    dirs = [ x for x in listdir('/test_dir_executed') if x.endswith('+') and path.isdir(path.join('/test_dir_executed', x)) ]
    print(dirs)

    #
    for dir in dirs:
      # именем каталога является id соответствующего TaskAnswer
      try:
        task_answer = TaskAnswer.objects.get(pk=int(dir[:-1]))
      except:
        print('pk dir')
        return

      assert(task_answer.task.execute_answer)

      files = listdir(path.join('/test_dir_executed', dir))
      try:
        [ int(filename) for filename in files ]
      except:
        print('files')
        return

      files.sort()
      assert(all(str(x1) == str(x2) for (x1, x2) in zip(files, range(len(files)))))
      assert(len(files) == task_answer.task.task_tests.count())

      # вывод при запуске на тестах обозначаемых от 0 до n-1
      outputs = []
      for file in files:
        with open(path.join('/test_dir_executed', dir, file), 'rt') as fin:
          outputs.append(fin.read())

      #
      task_test_executions = []
      for i, task_test in enumerate(task_answer.task.task_tests.all().order_by('id')):
        task_test_executions.append(TaskTestExecution(
          task_test=task_test,
          task_answer=task_answer,
          stdout=outputs[i],
          stderr='',
          returncode=0,
          execution_result='0' if task_test.output == outputs[i] else '1',
          duration=timedelta(seconds=1),
          memory_Kbyte=1024,
      ))

      # записываем в БД результаты запуска тестов. учитывать batch_size
      task_answer.task_answer_executions.all().delete()
      TaskTestExecution.objects.bulk_create(task_test_executions)

      # ставим макс. оценку если везде вывод совпадает, иначе 0
      #success = all(x.execution_result == '0' for x in task_test_executions)

      task_answer.is_running = False
      task_answer.save(update_fields=['is_running'])

      dir_res = path.join('/test_dir_executed', dir)
      rename(dir_res, dir_res[:-1])


#@shared_task(name='everyday')
@app.task
def everyday() -> None:
    """периодическое удаление данных с сервера"""
    print('everyday start')

    return
    # удаление помеченных записей из БД
    # если не переопределён delete, нет каскадного удаления и сигналов, то можно удалять in bulk через QuerySet?
    Comment.objects.filter(deleted=True).delete()
    Notification.objects.filter(deleted=True).delete()
    #TaskAnswer.objects.filter(deleted=True).delete()
    #TaskAnswerMark.objects.filter().delete()
    #TaskTestExecution.objects.filter(deleted=True).delete()

    # отправить напоминание об удалении аккаунта

    # удаление неактивных пользователей
    #User.objects.filter(is_active=False).delete()

    # удаление файлов с сервера
    files = [ FileStorage.objects.filter(deleted=True) ]
    FileStorage.objects.filter(id__in=[ file.id for file in files ]).delete()
    for file in files:
      file_path = os.path.join(settings.MEDIA_ROOT, str(file))

      try:
        os.remove(file_path)
      except Exception as e:
        print(e)

    print('everyday end')