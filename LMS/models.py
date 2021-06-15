from decimal import Decimal
from datetime import timedelta
import logging
import random
import re

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from django.db import models
from django.db.models import Sum

from .validators import validate_datetime_future

logger = logging.getLogger(__name__)


PROGRAMMING_LANGUAGE = [
    ('1', 'python 3.9.5'),
]

# python 3.9.5
SAFE_IMPORTS = [
    'string', # Common string operations
    're', # Regular expression operations
    'enum', # Support for enumerations
    'datetime', # Basic date and time types

    # Numeric and Mathematical Modules
    'numbers', # Numeric abstract base classes
    'math', # Mathematical functions
    'cmath', # Mathematical functions for complex numbers
    'decimal', # Decimal fixed point and floating point arithmetic
    'fractions', # Rational numbers
    'random', # Generate pseudo-random numbers
    'statistics', # Mathematical statistics functions

    'itertools', # Functions creating iterators for efficient looping
    'csv', # CSV File Reading and Writing
]

NOT_ALLOW_BUILT_IN_FUNCTIONS = [
    'compile',
    'eval',
    'exec',
    'globals',
    'help',
    'locals',
    'open',
    'vars',
    '__import__',
]

# deprecate: can_edit, is_subscriber
# после отписки от курса весь контент пользователя остаётся
class Course(models.Model):
    '''модель для учебного курса'''
    title = models.CharField('заголовок', help_text='max length 100', max_length=100, unique=True, validators=[RegexValidator(r'^.{1,100}$')])
    description = models.TextField('описание', help_text='max length 1000', max_length=1000, blank=True)
    #visible = models.BooleanField('страницу курса можно просматривать без записи', help_text='страницу курса можно просматривать без записи', default=True)

    owners = models.ManyToManyField(User, related_name='owners', verbose_name='преподаватели курса', blank=True)
    students = models.ManyToManyField(User, related_name='students', verbose_name='записанные студенты', blank=True)
    excluded = models.ManyToManyField(User, related_name='excluded', verbose_name='пользователи которым ограничен доступ к курсу', blank=True)

    # два способа записаться на курс: если пользователь состоит в одной из избранных групп или по секретному коду
    # если группы и код не указаны, то записаться может любой зарегистрированный
    # группы и секретный код выбирает преподаватель. создаёт группы и добавляет в них админ
    groups = models.ManyToManyField(Group, related_name='course_groups', verbose_name='группы которые могут записаться на курс', blank=True)
    key = models.CharField('код для записи на курс', help_text='length 5..20', max_length=20, validators=[RegexValidator(r'^.{5,20}$')], null=True, blank=True)

    class Meta:
        verbose_name = 'курс'
        verbose_name_plural = 'курсы'
        #ordering = ['id']

        # вроде можно использовать эти методы
        # https://docs.djangoproject.com/en/3.2/ref/models/querysets/#field-lookups
        constraints = [
            models.CheckConstraint(check=models.Q(title__regex=r'^.{1,100}$'), name='Course: title'),
            models.CheckConstraint(check=models.Q(key__regex=r'^.{5,20}$'), name='Course: key'),
        ]

    def __str__(self):
        return self.title

    def can_edit(self, user) -> bool:
        '''проверка прав на редактирование курса'''
        return self.owners.filter(pk=user.pk).exists()

    def is_subscriber(self, user) -> bool:
        '''проверка того что пользователь записан на курс'''
        return user.is_authenticated and self.students.filter(pk=user.pk).exists()

class CourseElement(models.Model):
    '''модель для элемента учебного курса'''
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='курс', related_name='course_elements')
    title = models.CharField('заголовок', max_length=100, help_text='max length 100', validators=[RegexValidator(r'^.{1,100}$')])
    description = models.TextField('описание', max_length=500, blank=True, help_text='max length 500')

    # через данное поле получаем файлы прикреплённые к элементу курса
    files = models.ManyToManyField('FileStorage', blank=True, verbose_name='прикреплённые к элементу файлы') # lazy reference

    class Meta:
        verbose_name = 'элемент курса'
        verbose_name_plural = 'элементы курсов'
        unique_together = ('course', 'title')
        #ordering = ['course']

        constraints = [
            models.CheckConstraint(check=models.Q(title__regex = r'^.{1,100}$'), name='CourseElement: title'),
        ]

    def __str__(self):
        return self.course.title + '. ' + self.title

    def description_rows(self):
        return self.description.split('\n')


# deprecate: can_edit_task, can_set_task_answer, get_answer, get_mark
class Task(models.Model):
    '''
    все действия с заданиями происходят через этот класс

    пользователь может загрузить ответ, если не наступило время deadline_true
    пользователь может изменить свой ответ, если не наступило время deadline_true и ответ не был оценен

    задание может быть с автоматической проверкой и без
    для автоматической проверки:
    - ввод с html страницы
    - не более 100 тестов
    - если тестов нет, то автоматическая проверка не запускается
    '''
    course_element = models.ForeignKey(CourseElement, on_delete=models.CASCADE, verbose_name='элемент курса', related_name='tasks')
    title = models.CharField('заголовок', help_text='max length 100', max_length=100, validators=[RegexValidator(r'^.{1,100}$')])
    description = models.TextField('описание задачи', help_text='max length 1000', max_length=1000, blank=True)
    execute_answer = models.BooleanField('включена автоматическая проверка', default=False)
    comments_is_on = models.BooleanField('комментарии включены', default=False)

    deadline_visible = models.DateTimeField('видимый срок сдачи', help_text='должно быть больше текущего времени на сервере UTC+3')#, validators=[validate_datetime_future])
    deadline_true = models.DateTimeField('последний срок сдачи', help_text='должно быть больше текущего времени на сервере UTC+3')#, validators=[validate_datetime_future])

    mark_outer = models.DecimalField('максимальные чистые баллы', help_text='decimal from 0.00 to 999.99', max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    mark_max = models.DecimalField('максимальные грязные баллы', help_text='decimal from 0.00 to 999.99', max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])

    # поля для ручной проверки ответов
    limit_files_count = models.PositiveSmallIntegerField('макс кол-во файлов', help_text='integer from 1 to 32', default=4, validators=[MinValueValidator(1), MaxValueValidator(32)])
    limit_files_memory_MB = models.PositiveSmallIntegerField('ограничение размера ответа в МБ', help_text='integer from 1 to 128', default=4, validators=[MinValueValidator(1), MaxValueValidator(128)])

    # поля для автоматической проверки ответов
    start_code = models.TextField('начальное значение в поле для кода', help_text='max length 1000', max_length=1000, blank=True)

    # ограничения на выполнение кода
    #STACK_SIZE = [
    #    ('1024', '1024'),
    #    ('2048', '2048'),
    #    ('4096', '4096'),
    #    ('8192', '8192'),
    #    ('16384', '16384'),
    #    ('32768', '32768'),
    #]
    #STACK_Kbyte = models.CharField('размер стека в КБ', max_length=5, choices=STACK_SIZE, default='8192')
    limit_time = models.DurationField('ограничение времени выполнения', help_text='format HH:MM:SS.uuuuuu \ 1sec <= value <= 10sec', validators=[MinValueValidator(timedelta(seconds=1)), MaxValueValidator(timedelta(seconds=10))], default=timedelta(seconds=1))
    limit_memory_Mbyte = models.PositiveSmallIntegerField('ограничение памяти в МБ', help_text='integer from 1 to 1024', validators=[MinValueValidator(1), MaxValueValidator(1024)], default=256)

    class Meta:
        verbose_name = 'задание'
        verbose_name_plural = 'задания'

        unique_together = ('course_element', 'title')

        # database constraints
        constraints = [
            models.CheckConstraint(check=models.Q(title__regex = r'^.{1,100}$'), name='Task: title'),
            models.CheckConstraint(check=models.Q(mark_outer__gte=Decimal(0)), name='Task: mark_outer__gte=0'),
            models.CheckConstraint(check=models.Q(mark_max__gte=Decimal(0)), name='Task: mark_max__gte=0'),

            models.CheckConstraint(
                check=models.Q(limit_files_count__gte=1) & models.Q(limit_files_count__lte=32),
                name='Task: limit_files_count__gte=1 & limit_files_count__lte=32'),

            models.CheckConstraint(
                check=models.Q(limit_files_memory_MB__gte=1) & models.Q(limit_files_memory_MB__lte=128),
                name='Task: limit_files_memory_MB_gte=0 & limit_files_memory_MB__lte=128'),

            models.CheckConstraint(
                check=models.Q(limit_time__gte=timedelta(seconds=1)) & models.Q(limit_time__lte=timedelta(seconds=10)), 
                name='Task: limit_time__gt=timedelta(seconds=1) & limit_time__lte=timedelta(seconds=10)'),

            models.CheckConstraint(
                check=models.Q(limit_memory_Mbyte__gte=1) & models.Q(limit_memory_Mbyte__lte=1024),
                name='Task: limit_memory_Mbyte__gte=1 & limit_memory_Mbyte__lte=1024'),
        ]

    def __str__(self):
        return self.course_element.course.title + '. ' + self.title

    def clean(self):
        """model validation"""
        super(Task, self).clean() # проверки полей

        if self.execute_answer: # None?
            pass
        else:
            pass

        if self.deadline_visible and self.deadline_true and self.deadline_true < self.deadline_visible:
            raise ValidationError({'deadline_true':'deadline_true < deadline_visible'})

    def can_edit_task(self, user) -> bool:
        '''проверка прав на редактирование задачи курса +'''
        return self.course_element.course.can_edit(user)

    def can_set_task_answer(self, user) -> bool:
        '''пользователь может загрузить на сервер ответ на задание +'''
        if self.deadline_true < timezone.now():
            return False

        taskAnswer = TaskAnswer.objects.filter(task=self, student=user).first()
        # в автоматической проверке если выполняется или есть оценка то нельзя
        if taskAnswer and taskAnswer.task.execute_answer:
            return not taskAnswer.is_running and taskAnswer.get_TaskAnswerMark() is None
        else:
            return True if taskAnswer is None or taskAnswer.get_TaskAnswerMark() is None else False

    def get_answer(self, user):
        '''возвращает ответ на задание или None если ответа нет. В TaskAnswer (task, user) = unique +'''
        return TaskAnswer.objects.filter(task=self, student=user).first()

    def get_mark(self, user):
        '''возвращает число-оценку за задание если оно завершено, иначе возвращает None +'''
        taskAnswer = TaskAnswer.objects.filter(task=self, student=user).first()
        if taskAnswer is None:
            return None if timezone.now() < self.deadline_true else Decimal(0)

        taskAnswerMark = taskAnswer.get_TaskAnswerMark()
        return taskAnswerMark.mark / self.mark_max * self.mark_outer if taskAnswerMark else None

class TaskTest(models.Model):
    '''
    тест для задания с автоматической проверкой
    содержит входные данные программы и ожидаемый от неё вывод
    '''
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name='задание', related_name='task_tests')
    input = models.TextField('входные данные программы', help_text='max length 1000', max_length=1000) # может быть пустым
    output= models.TextField('ожидаемый вывод программы', help_text='max length 1000', max_length=1000) # не может быть пустым
    hidden = models.BooleanField('скрытый тест (пользователям отображается не будет)')#, default=True)

    class Meta:
        verbose_name = 'тест для задания с автоматической проверкой'
        verbose_name_plural = 'тесты для заданий с автоматической проверкой'

    def __str__(self):
        return self.task.__str__() + ' | ' + self.id.__str__()

    def clean(self):
        """model validation"""
        super(TaskTest, self).clean() # проверки полей

        if self.task and not self.task.execute_answer:
            raise ValidationError({'task':'выбранное задание без автоматической проверки'})

        if 100 < TaskTest.objects.filter(task=self.task).count():
            raise ValidationError({'__all__':'ограничение на 100 тестов для задачи'})

class TaskTestExecution(models.Model):
    '''
    тест для задания с автоматической проверкой
    содержит входные данные для программы и ожидаемый от неё вывод
    '''
    task_test = models.ForeignKey(TaskTest, on_delete=models.CASCADE, verbose_name='тест задания') # editable=False
    task_answer = models.ForeignKey('TaskAnswer', on_delete=models.CASCADE, verbose_name='ответ на задание', related_name='task_answer_executions') # editable=False

    stdout = models.TextField('стандартный поток вывода', help_text='max length 1000', max_length=1000)
    stderr = models.TextField('поток вывода ошибок', help_text='max length 100', max_length=100)
    returncode = models.IntegerField()

    EXECUTION_RESULT = [
        ('0', 'accepted'),
        ('1', 'wrong answer'),
        ('2', 'time limit'),
        ('3', 'memory limit'),
        ('4', 'compile_error'),
        ('5', 'execution_error'),
        ('6', 'running'),
        ('7', 'other'),
    ]

    execution_result = models.CharField('execution_result', max_length=1, choices=EXECUTION_RESULT, default='6')
    duration = models.DurationField('время работы программы', validators=[MinValueValidator(timedelta())], help_text='format HH:MM:SS.uuuuuu')
    memory_Kbyte = models.PositiveBigIntegerField('выделено памяти в байтах')

    class Meta:
        verbose_name = 'выполнение теста для задания с автоматической проверкой'
        verbose_name_plural = 'выполнения тестов для заданий с автоматической проверкой'

        unique_together = ('task_test', 'task_answer')

        # database constraints
        constraints = [
            models.CheckConstraint(check=models.Q(duration__gte=timedelta()), name='TaskTestExecution: duration__gte=timedelta()'),
        ]

    def __str__(self):
        return self.task_test.__str__() + self.id.__str__()

class TaskAnswer(models.Model):
    '''ответ на задание'''
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name='задание', related_name='task_answers')
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='студент')
    datetime_load = models.DateTimeField('дата и время ответа', help_text='время выставляется автоматически во время создания/изменения объекта', auto_now=True)
    #deleted = models.BooleanField('удалено', help_text='запись удалится по расписанию', default=False, editable=False)

    # для ручной проверки
    files = models.ManyToManyField('FileStorage', related_name='task_answers_files', verbose_name='загруженные файлы', blank=True, editable=False)

    # для автоматической проверки
    language = models.CharField('язык программирования', max_length=1, choices=PROGRAMMING_LANGUAGE, null=True, blank=True) # editable=False
    code = models.TextField('ответ на задачу в виде кода', help_text='max length 1000', max_length=1000, blank=True) # editable=False
    is_running = models.BooleanField('код выполняется', default=False)

    class Meta:
        verbose_name = 'ответ на задание'
        verbose_name_plural = 'ответы на задания'

        unique_together = ('task', 'student')

    def __str__(self):
        return self.task.__str__() + ' | ' + self.student.__str__()

    def clean(self):
        """model validation"""
        super(TaskAnswer, self).clean() # проверки полей модели
        validation_errors = dict()

        if not self.task.course_element.course.is_subscriber(self.student):
            validation_errors['student'] = ValidationError('задание только для записанных на курс')

        #if self.datetime_load and self.task.deadline_true < self.datetime_load:
        #    validation_errors['datetime_load'] = ValidationError('дедлайн прошёл')

        if not self.datetime_load and self.task.deadline_true < timezone.now():
            validation_errors['datetime_load'] = ValidationError('дедлайн прошёл')

        if TaskAnswerMark.objects.filter(task_answer_id=self.id).exists():
            validation_errors['__all__'] = ValidationError('ответ на это задание уже оценили')

        # задание с автоматической проверкой
        if self.task.execute_answer:
            code_errors = []
            if self.code == '':
                code_errors.append(ValidationError('Обязательное поле.'))
            else:
                # проверка импортов модулей
                import_lines = re.findall(r'\Wfrom|import.*$', self.code)

                for line in import_lines:
                    if not all( x in SAFE_IMPORTS+['from', 'import', 'as'] for x in re.split(r'\W+', line)):
                        code_errors.append(ValidationError('import now allowed'))

                # проверка Built-in Functions
                for s in NOT_ALLOW_BUILT_IN_FUNCTIONS:
                    if re.search(r'^_pref_\(|[^a-z0-9]_pref_\('.replace('_pref_', s), self.code):
                        code_errors.append(ValidationError('this built-in function not allowed'))

            if 0 < len(code_errors):
                validation_errors['code'] = code_errors

        # задание с ручной проверкой
        if not self.task.execute_answer:
            files_errors = []
            if self.files.all().count() == 0:
                files_errors.append(ValidationError('нет загруженных файлов для ручной проверки'))

            if self.task.limit_files_count < self.files.all().count():
                message = f'Количество файлов в ответе на задание должно быть не больше {self.task.limit_files_count}'
                files_errors.append(ValidationError(message))

            # не должно быть пустых файлов
            #if 0 < self.files.all().count() and self.files.filter(file__size=0).exists():
            #    message = f'Не должно быть пустых файлов'
            #    files_errors.append(ValidationError(message))

            # refactoring: подсчёт суммы делать с помощью aggregate
            if 0 < self.files.all().count() and self.task.limit_files_memory_MB*1024*1024 < sum(fileStorage.file.size for fileStorage in self.files.all()):
                message = f'Размер файлов в ответе на задание в сумме не должен превышать {self.task.limit_files_memory_MB*1024*1024}'
                files_errors.append(ValidationError(message))

            if 0 < len(files_errors):
                validation_errors['files'] = files_errors

        if 0 < len(validation_errors):
            raise ValidationError(validation_errors)

    def get_TaskAnswerMark(self):
        ''''''
        return TaskAnswerMark.objects.filter(task_answer_id=self.id).first()

class TaskAnswerMark(models.Model):
    '''оценка за ответ на задание'''
    task_answer = models.OneToOneField(TaskAnswer, on_delete=models.CASCADE, verbose_name='ответ на задание', related_name='task_answer_mark')

    teacher = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='преподаватель', null=True, help_text='null если автоматич проверка')
    mark = models.DecimalField('оценка в грязных баллах', help_text='decimal xxx.xx', max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    review = models.CharField('отзыв преподавателя', max_length=255, help_text='max length 255', blank=True)

    # препод может оценить задание в любое время после загрузки ответа
    datetime_evaluate = models.DateTimeField('дата и время выставления оценки', help_text='время выставляется автоматически во время создания объекта', auto_now=True)

    class Meta:
        verbose_name = 'оценка за ответ на задание'
        verbose_name_plural = 'оценки за ответы на задания'

        # database constraints
        constraints = [
            models.CheckConstraint(check=models.Q(mark__gte=Decimal(0)), name='TaskAnswerMark: mark__gte=0'),
        ]

    def __str__(self):
        return self.task_answer.__str__()

    def clean(self):
        """проверки модели"""
        super(TaskAnswerMark, self).clean() # проверки полей модели
        validation_errors = dict()

        if not self.teacher or not self.task_answer.task.course_element.course.can_edit(self.teacher):
            validation_errors['teacher'] = ValidationError('указанный пользователь не имеет права на выставление оценки')

        mark_max = self.task_answer.task.mark_max
        if mark_max < self.mark:
            validation_errors['mark'] = ValidationError(f'оценка должна быть меньше или равна {mark_max}')

        if 0 < len(validation_errors):
            raise ValidationError(validation_errors)

    def save(self, *args, **kwargs):
        """"""
        # сохраняем оценку в БД
        super(TaskAnswerMark, self).save(*args, **kwargs)

        # создаём уведомление об оценивании
        if not self.task_answer.task.execute_answer:
            Notification.objects.create(user=self.task_answer.student, text=f"оценили задание с id {self.id}")

    def dot_mark(self) -> str:
        """временный костыль для повторного оценивания задачи"""
        return str(self.mark).replace(',', '.')


# todo: переопределить методы update/delete или добавить сигналы
# deprecate: can_edit, get_test_max_mark, get_user_mark, get_finished_test_results, get_active_test_result, can_start_new_test, start_new_test
# https://docs.djangoproject.com/en/3.2/topics/db/models/#overriding-model-methods
class Test(models.Model):
    """
    - не менее 1 и не более 70 вопросов
    - до начала теста его можно изменить и удалить
    - после наступления времени start нельзя изменять тест и вопросы к нему
    - todo: в методе save данного класса создаётся тест и вопросы к тесту
    """
    course_element = models.ForeignKey(CourseElement, on_delete=models.CASCADE, verbose_name='элемент курса', related_name='tests')
    title = models.CharField('заголовок', help_text='max length 100', max_length=100, validators=[RegexValidator(r'^.{1,100}$')])

    # пояснения, замечания и прочее что нужно знать перед прохождением теста
    description = models.TextField('инфа к тесту', help_text='max length 1000', max_length=1000, blank=True)

    mark_outer = models.DecimalField('чистые баллы', help_text='decimal from 0.00 to 999.99', max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    number_of_attempts = models.PositiveSmallIntegerField('кол-во попыток', help_text='from 1 to 10', default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    shuffle = models.BooleanField('вопросы будут отображаться в случ. порядке', default=True)

    TEST_TYPE = [
        ('one', 'отвечать один раз в прямом порядке'),
        ('many', 'отвечать в любом порядке. можно изменять ответ'),
    ]
    test_type = models.CharField('тип теста', max_length=4, choices=TEST_TYPE)

    # после наступления времени start тест нельзя менять
    start = models.DateTimeField('начало тестирования', help_text='должно быть больше текущего времени на сервере UTC+3', validators=[validate_datetime_future])
    end = models.DateTimeField('окончание тестирования', help_text='должно быть больше текущего времени на сервере UTC+3', validators=[validate_datetime_future])
    duration = models.DurationField('время на прохождение теста', help_text='format HH:MM:SS.uuuuuu \  1sec <= value <= 24 hours', validators=[MinValueValidator(timedelta(seconds=1)), MaxValueValidator(timedelta(hours=24))])

    class Meta:
        verbose_name = 'тест'
        verbose_name_plural = 'тесты'

        unique_together = ('course_element', 'title')

        # database constraints
        constraints = [
            models.CheckConstraint(check=models.Q(title__regex = r'^.{1,100}$'), name='Test: title'),
            models.CheckConstraint(check=models.Q(mark_outer__gte=Decimal(0)), name='Test: mark_outer__gte=0'),

            models.CheckConstraint(
                check=models.Q(number_of_attempts__gt=0) & models.Q(number_of_attempts__lt=11),
                name='Test: number_of_attempts__gt=0 & models.Q(number_of_attempts__lt=11)'),

            models.CheckConstraint(
                check=models.Q(duration__gte=timedelta(seconds=1)) & models.Q(duration__lte=timedelta(hours=24)),
                name='Test: duration__gte=timedelta(seconds=1) & duration__lte=timedelta(hours=24)'),
        ]

    def __str__(self):
        return self.course_element.course.title + '. ' + self.title

    def clean(self):
        """model validation. проверка объекта целиком. при создании объекта проиходит проверка"""
        super(Test, self).clean() # проверки полей модели

        validation_errors = dict()

        if self.end <= self.start:
            validation_errors['end'] = ValidationError('start < end')

        if self.end - self.start < self.duration:
            validation_errors['duration'] = ValidationError('duration <= end-start')

        if self.start <= timezone.now():
            validation_errors['__all__'] = ValidationError('test started. cannot change test')

        if 0 < len(validation_errors):
            raise ValidationError(validation_errors)


    def can_edit(self, user) -> bool:
        '''проверка прав на редактирование'''
        return self.course_element.course.can_edit(user) and timezone.now() < self.start

    def get_test_max_mark(self) -> Decimal:
        '''возвращает максимум грязных баллов за тест. равно сумме грязных баллов по вопросам теста'''
        return TestQuestion.objects.filter(test=self).aggregate(Sum('max_mark'))['max_mark__sum']

    def get_user_mark(self, user) -> Decimal:
        '''возвращает наибольшую оценку пользователя за тест. если нет завершённых попыткок и время не закончилось, то None. если нет попыток и время закончилось, то 0'''

        # дедлайн теста наступил
        if self.end < timezone.now():
            marks = [ x.evaluate_mark() for x in TestResult.objects.filter(test=self, user=user) ]
            return Decimal(0) if len(marks) == 0 else max(marks)

        # дедлайн теста не наступил. есть завершённые прохождения теста
        testResults = self.get_finished_test_results(user)
        if 0 < len(testResults):
            return max(testResult.evaluate_mark() for testResult in testResults)

        # дедлайн теста не наступил. нет завершённых прохождений теста
        return None

    def get_finished_test_results(self, user) -> list:
        '''возвращает завершённые попытки (завершено или вышло время)'''
        now = timezone.now()
        res = [ x for x in TestResult.objects.filter(test=self, user=user) if x.end != None or x.start + x.test.duration < now ]
        return res

    def get_active_test_result(self, user):
        '''возвращает начатое прохождение этого теста или None'''
        if self.end < timezone.now():
            return None

        now = timezone.now()
        res = [ x for x in TestResult.objects.filter(test=self, user=user) if x.end == None and now < x.start + self.duration ]
        return res[0] if 0 < len(res) else None
    
    def can_start_new_test(self, user) -> bool:
        '''может ли пользователь начать новое прохождение теста. начатые попытки должны закрыться, остаться нетронутые попытки, тест начался и ещё не завершился'''
        now = timezone.now()
        return self.start < now and now < self.end and 0 < (self.number_of_attempts - len(self.get_finished_test_results(user))) and self.get_active_test_result(user) == None

    def start_new_test(self, user):
        '''возвращает новый TestResult или None, если пользователь не может начать попытку'''
        if self.can_start_new_test(user):
            test_result = TestResult.objects.create(
                test_id=self.id,
                user=user,
                start=timezone.now(),
            )
            # определяем порядок вопросов в прохождении
            questions = test_result.test.test_questions.all().order_by('id')

            if self.shuffle:
                questions_order = list(range(self.test_questions.count()))
                random.shuffle(questions_order)

                questions_initial = list(questions)
                questions = [questions_initial[i] for i in questions_order]

            # создаём записи под ответы для данного прохождения теста
            test_question_answers = (TestQuestionAnswer(test_result=test_result, test_question=q) for q in questions)
            TestQuestionAnswer.objects.bulk_create(test_question_answers)

            return test_result
        else:
            return None

# deprecate: evaluate_mark, complete, is_finished
class TestResult(models.Model):
    """
    Результат прохождения одной попытки теста.
    -запись активна, если не наступило время task.end, self.end == None и со времени self.start прошло не больше task.duration
    -запись завершена, если наступило время task.end,  self.end != None или со времени self.start прошло task.duration
    """
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='тест')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='тестируемый')

    # оценку можно выставить вручную. у неё будет приоритет
    mark = models.DecimalField('ручная оценка в чистых баллах', help_text='decimal xxx.xx', max_digits=5, decimal_places=2, validators=[MinValueValidator(0)], null=True, default=None)
    
    start = models.DateTimeField('начало прохождения теста', help_text='время выставляется автоматически во время создания объекта', auto_now_add=True)
    end = models.DateTimeField('окончание прохождения теста', help_text='заполняется если тестируемый нажал завершить во время прохождения теста', null=True, editable=False)

    class Meta:
        verbose_name = 'результат тестирования'
        verbose_name_plural = 'результаты тестирования'

        constraints = [
            models.CheckConstraint(check=models.Q(mark__gte=Decimal(0)), name='TestResult: mark__gte=0'),
        ]

    def __str__(self):
        return self.test.__str__() + ' | ' + self.user.__str__() + ' | ' + str(self.start)

    def clean(self):
        """проверка данных модели"""
        super(TestResult, self).clean() # проверки полей модели
        validation_errors = dict()

        # проверить права юзера на создание нового прохождения

        # допустимое значение оценки если она есть
        if self.mark and self.test.mark_outer < self.mark:
            validation_errors['mark'] = ValidationError(f'оценка должна быть меньше или равна {self.test.mark_outer}')

        # прохождение начато в допустимые сроки
        if self.start < self.test.start or self.test.end < self.start:
            validation_errors['start'] = ValidationError(f'start must be in correct time. between {self.test.start} and {self.test.end}')

        # прохождение закончено в допустимые сроки
        if self.end:
            if self.end < self.start or self.test.end < self.end or self.test.duration < (self.end - self.start):
                validation_errors['end'] = ValidationError('incorrect')
        
        if 0 < len(validation_errors):
            raise ValidationError(validation_errors)

    def save(self, *args, **kwargs):
        will_be_created = self.id is None

        super(TestResult, self).save(*args, **kwargs)

        # объект создан. в тестах вручную создаются TestQuestionAnswer из-за этого исключение бросает
        if will_be_created:
            if self.test.shuffle:
                pass
            else:
                #test_question_answers = [ TestQuestionAnswer(test_result=self, test_question=q) for q in self.test.test_questions.all() ]
                #TestQuestionAnswer.objects.bulk_create(test_question_answers)
                pass


    def evaluate_mark(self) -> Decimal:
        '''вычисляет оценку в чистых баллах за данное проходение теста. если тест не завершён возвращает None'''
        # тест не завершён
        now = timezone.now()
        if self.end == None and now < self.test.end and now < self.start + self.test.duration:
            return None

        # тест оценил преподаватель
        if self.mark:
            return self.mark

        # автоматическое оценивание
        mark_sum = TestQuestionAnswer.objects.filter(test_result=self).aggregate(Sum('mark'))['mark__sum']
        return Decimal(0) if mark_sum is None else self.test.mark_outer * mark_sum / self.test.get_test_max_mark()

    def complete(self) -> None:
        '''завершить прохождение теста'''
        now = timezone.now()
        if now < self.test.end and now < self.start + self.test.duration:
            self.end = now
            self.save(update_fields=['end'])

    def is_finished(self) -> bool:
        '''завершено ли прохождение теста (вышло время или пользователь завершил попытку)'''
        now = timezone.now()
        return self.end != None or self.test.end < now or self.start + self.test.duration < now

class TestQuestion(models.Model):
    """
    вопрос теста
    - вопросы можно создавать, изменять и удалять только если тест ещё не начался
    - 2..10 вариантов ответов. 1..150 символов на вариант ответа (нельзя использ. символ \\n)
    - свободный ответ не более 50 символов
    """
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='тест', related_name='test_questions')
    #order = models.PositiveSmallIntegerField('номер вопроса в тесте', help_text='заполняется автоматически') # editable=False) # from 0 to 32767
    question_text = models.TextField('текст вопроса', help_text='max length 500', max_length=500, validators=[MinLengthValidator(1)])

    max_mark = models.DecimalField('максимальное кол-во грязных баллов за вопрос', help_text='decimal from 0.00 to 999.99', max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])

    # правильный выбор: пропорционально от всех правильных ответов
    # штраф за неправильный выбор:
    # - отнять стоимость одного правильного ответа
    # - отнять все баллы
    QUESTION_TYPE = [
        ('free', 'свободный ответ'),
        ('one', 'выбор одного ответа'),

        ('many1', 'выбор нескольких ответов (не менее 2) (штраф за неправильный выбор - стоимость одного правильного ответа)'),
        ('many2', 'выбор нескольких ответов (не менее 2) (штраф за неправильный выбор - все баллы)'),
    ]
    answer_type = models.CharField('тип вопроса', max_length=5, choices=QUESTION_TYPE)

    # free: пустая строка
    # one, many: 2..10 вариантов ответов на вопрос, разделённые между собой \n
    answer_values = models.TextField(
        'варианты ответов',
        help_text='варианты ответов на вопрос, разделённы между собой символом перевода строки. при свободном ответе 0 символов в поле',
        max_length=150*10+9,
        blank=True,
    )

    # текстовое поле интерпретируется в зависимости от answer_type
    # free: строка
    # one:  индекс правильного варианта ответа. индексы с 0
    # many: индексы правильных вариантов через пробел. индексы с 0 
    answer_true = models.CharField(
        'правильный ответ',
        help_text='индексы правильных вариантов через пробел (начинаются с 0). при свободном ответе строка-значение',
        max_length=50,
    )

    class Meta:
        verbose_name = 'вопрос теста'
        verbose_name_plural = 'вопросы тестов'

        #unique_together = ('test', 'order')

        # database constraints
        constraints = [
            models.CheckConstraint(check=models.Q(question_text__gte=1), name='TestQuestion: question_text__gte=1'),
            models.CheckConstraint(check=models.Q(max_mark__gte=Decimal(0)), name='TestQuestion: max_mark__gte=0'),
        ]

    def __str__(self):
        return self.question_text

    # рег. выраж. допуск. пробелы в начале и конце строки
    def clean(self):
        """проверка данных модели"""
        super(TestQuestion, self).clean() # проверки всех полей модели по одной
        validation_errors = dict()

        if self.test.start <= timezone.now():
            validation_errors['__all__'] = ValidationError('после начала теста его нельзя изменять')

        # проверить варианты ответов, т.е. self.answer_values
        free_valid   = self.answer_type == 'free' and self.answer_values == ''
        choice_valid = self.answer_type != 'free' and re.fullmatch(r'^(.{1,150}\n){1,9}.{1,150}$', self.answer_values)
        if self.answer_type != 'free' and self.answer_values == '':
            validation_errors['answer_values'] = ValidationError('Обязательное поле.')
        elif not free_valid and not choice_valid:
            validation_errors['answer_values'] = ValidationError('incorrect')

        # проверить правильный ответ, т.е. self.answer_true
        free_valid = self.answer_type == 'free' and re.fullmatch(r'^.{1,50}$', self.answer_true)
        one_valid, many1_valid, many2_valid  = False, False, False

        if not free_valid:
            #1.правильный формат
            #2.индексы в допустимых пределах
            #3.нет повторов
            valid_format = re.fullmatch(r'^(\d+ )*\d+$', self.answer_true)
            if valid_format:
                indexes = [ int(x) for x in self.answer_true.split(' ') ] # regex гарантирует что один пробел между индексами

                answers_count = self.answer_values.count('\n') + 1
                is_border = all(0 <= x and x < answers_count for x in indexes)
                is_unique = len(indexes) == len(set(indexes))

                one_valid   = self.answer_type == 'one'   and len(indexes) == 1 and is_border
                many1_valid = self.answer_type == 'many1' and len(indexes) <= answers_count and is_border and is_unique
                many2_valid = self.answer_type == 'many2' and len(indexes) <= answers_count and is_border and is_unique
                #print(valid_format,self.answer_true, '_', answers_count, is_unique, is_border, one_valid, many1_valid, many2_valid)

        if self.answer_true != '' and not free_valid and not one_valid and not many1_valid and not many2_valid:
            validation_errors['answer_true'] = ValidationError('incorrect')

        if 0 < len(validation_errors):
            raise ValidationError(validation_errors)

class TestQuestionAnswer(models.Model):
    '''ответ на вопрос теста'''
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, verbose_name='прохождение теста', related_name='test_result_questions_answers')
    test_question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, verbose_name='вопрос теста')
    datetime = models.DateTimeField('время ответа на вопрос', help_text='время выставляется автоматически во время создания/изменения объекта', null=True)

    # free: свободный ответ
    # one, many1, many2: индексы выбранных вариантов ответов через пробел
    answer = models.CharField('ответ на вопрос', max_length=50, help_text='индексы выбранных вариантов ответов через пробел или значение свободного ответа')

    # вычисляется автоматически по значению self.answer (см. переопределение метода save)
    mark = models.DecimalField('баллы за вопрос', max_digits=5, decimal_places=2, help_text='вычисляется автоматически', validators=[MinValueValidator(0)], null=True, blank=True, default=None)

    class Meta:
        verbose_name = 'ответ на вопрос теста'
        verbose_name_plural = 'ответы на вопросы тестов'

        unique_together = ('test_result', 'test_question')

        # database constraints
        constraints = [
            models.CheckConstraint(check=models.Q(mark__gte=Decimal(0)), name='TestQuestionAnswer: mark__gte=0'),
        ]

    def __str__(self):
        return self.test_result.__str__() + ' | ' + self.test_question.__str__()

    def clean(self):
        """проверка данных модели"""
        super(TestQuestionAnswer, self).clean() # проверки полей модели
        validation_errors = dict()

        # проверить окончание попытки теста
        if self.test_result.is_finished():
            validation_errors['__all__'] = ValidationError('test finished')

        # проверить формат self.answer
        if self.answer != '' and self.test_question.answer_type != 'free':
            #1.правильный формат
            #2.индексы в допустимых пределах
            #3.нет повторов
            one_valid, many1_valid, many2_valid  = False, False, False

            valid_format = re.fullmatch(r'^(\d+ )*\d+$', self.answer)
            if valid_format:
                indexes = [ int(x) for x in self.answer.split(' ') ] # regex гарантирует что один пробел между индексами

                answers_count = self.test_question.answer_values.count('\n') + 1
                is_border = all(0 <= x and x < answers_count for x in indexes)
                is_unique = len(indexes) == len(set(indexes))

                one_valid   = self.test_question.answer_type == 'one'   and len(indexes) == 1 and is_border
                many1_valid = self.test_question.answer_type == 'many1' and len(indexes) <= answers_count and is_border and is_unique
                many2_valid = self.test_question.answer_type == 'many2' and len(indexes) <= answers_count and is_border and is_unique
                #print(valid_format,self.answer_true, '_', answers_count, is_unique, is_border, one_valid, many1_valid, many2_valid)

            if not one_valid and not many1_valid and not many2_valid:
                validation_errors['answer'] = ValidationError('incorrect')
        
        if 0 < len(validation_errors):
            raise ValidationError(validation_errors)

    # не вызывается во время bulk_create
    def save(self, *args, **kwargs):
        if self.answer != '':
            # вычисляем self.mark. считаем что данные корректные
            q = self.test_question
            q_type = q.answer_type

            if q_type == 'free' or q_type == 'one':
                self.mark = q.max_mark if q.answer_true.strip() == self.answer.strip() else Decimal(0)
            else:
                answer_indexes = set(int(x) for x in self.answer.strip().split(' '))
                true_indexes = set(int(x) for x in q.answer_true.strip().split(' '))

                choise_true = len(answer_indexes & true_indexes) # кол-во правильных вариантов
                choise_false = len(answer_indexes - true_indexes) # кол-во неправильных вариантов

                if q_type == 'many1':
                    # деление на ноль
                    self.mark = Decimal(max(choise_true-choise_false, 0) / len(true_indexes)) * q.max_mark
                elif q_type == 'many2':
                    # деление на ноль
                    self.mark = Decimal(choise_true / len(true_indexes)) * q.max_mark if choise_false == 0 else Decimal(0)
                else:
                    raise Exception('QUESTION_TYPE')

        super(TestQuestionAnswer, self).save(*args, **kwargs)


class Notification(models.Model):
    '''Уведомления пользователей'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    text = models.CharField('текст уведомления', help_text='max length 255', max_length=255)
    datetime = models.DateTimeField('время создания', help_text='время выставляется автоматически во время создания объекта', auto_now_add=True)

    readed = models.BooleanField('прочитано', help_text='при создании уведомление не прочитано', default=False, editable=False)
    deleted = models.BooleanField('удалено', help_text='запись удалится по расписанию', default=False, editable=False)

    class Meta:
        verbose_name = 'уведомление пользователя'
        verbose_name_plural = 'уведомления пользователей'

    def __str__(self):
        return self.user.__str__() + ': ' + self.datetime.__str__()

class Comment(models.Model):
    '''
    Комментарии пользователей к заданиям
    - если пользователя удалить, то комментарии удалятся
    - owners курса могут скрывать комментарии в своих курсах
    - оставлять комментарии могут только подписанные на курс
    - упомянуть кого-то: $login . он получит уведомление
    '''
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField('текст комментария', help_text='max length 255. чтобы упомянуть кого-то: $login', max_length=255, validators=[MinLengthValidator(1)])
    datetime = models.DateTimeField('время написания', help_text='время выставляется автоматически во время создания объекта', auto_now_add=True)
    
    visible = models.BooleanField('коммент видно', help_text='препод может скрыть коммент', default=True)
    deleted = models.BooleanField('удалено', help_text='запись удалится по расписанию', default=False, editable=False)
    
    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

        constraints = [
            models.CheckConstraint(check=models.Q(text__gte=1), name='Comment: text__gte=1'),
        ]

    def __str__(self):
        return self.task.__str__() + ' | ' + self.user.__str__()

    def clean(self):
        """проверка данных модели"""
        super(Comment, self).clean() # проверки всех полей модели по одной
        validation_errors = dict()

        # проверить что комменты у задачи включены
        if not self.task.comments_is_on:
            validation_errors['task'] = ValidationError('комментарии отключены в задаче')

        # проверить что пользователь может оставлять комментарии (подписан на курс)
        if not self.task.course_element.course.students.filter(user=self.user).exists():
            validation_errors['user'] = ValidationError('пользователь не подписан на курс')
        
        if 0 < len(validation_errors):
            raise ValidationError(validation_errors)

    def save(self, *args, **kwargs):
        # сохраняем в БД комментарий
        super(Comment, self).save(*args, **kwargs)

        # если упоминается другой пользователь, то создать уведомление
        check_logins = [ word[1:] for word in self.text.split() if word.startswith('$') and 1 < len(word) ]
        if 0 < len(check_logins):
            users = User.objects.filter(username__in=check_logins).only('username')
            #users_id = User.objects.filter(username__in=check_logins).values_list('id', flat=True)
            notifications = [ Notification(user=user, text=f"вас упомянули в комментарии с id {self.id}") for user in users ]
            
            if 0 < len(users):
                Notification.objects.bulk_create(notifications)

class FileStorage(models.Model):
    '''модель для хранения файлов на сервере'''
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='пользователь загрузивший файл', null=True)
    datetime = models.DateTimeField('дата и время загрузки файла', help_text='время выставляется автоматически во время создания объекта', auto_now_add=True)
    file = models.FileField(upload_to='files')
    filename = models.CharField('имя файла при загрузке', max_length=255, help_text='max length 255', validators=[MinLengthValidator(1)])
    deleted = models.BooleanField('удалено', help_text='запись удалится по расписанию', default=False)

    course_element = models.ForeignKey(CourseElement, on_delete=models.SET_NULL, verbose_name='', null=True, blank=True)
    task_answer = models.ForeignKey(TaskAnswer, on_delete=models.SET_NULL, verbose_name='', null=True, blank=True)

    class Meta:
        verbose_name = 'загруженный файл'
        verbose_name_plural = 'загруженные файлы'

        constraints = [
            models.CheckConstraint(check=models.Q(filename__gte=1), name='FileStorage: filename__gte=1'),
        ]

    def __str__(self):
        return self.file.__str__()

    def clean(self):
        """проверка данных модели"""
        super(FileStorage, self).clean() # проверки всех полей модели по одной

        if self.course_element and self.task_answer:
            raise ValidationError('course_element & task_answer')

    def save(self, *args, **kwargs):
        """переопределение метода для записи в БД"""
        if self.file and self.filename == '' and hasattr(self.file, 'name'):
            self.filename = self.file.name # path, size
        super(FileStorage, self).save(*args, **kwargs)

class UserData(models.Model):
    '''Дополнительная инфа пользователя'''
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_data')

    dark_mode = models.BooleanField(default=False)
    send_notifications_to_email = models.BooleanField(default=True)

    TIME_CHOICES = [
        ('3', '3'),
        ('6', '6'),
        ('12', '12'),
        ('18', '18'),
    ]
    delete_time = models.CharField(max_length=2, choices=TIME_CHOICES, null=True, blank=True)

    class Meta:
        verbose_name = 'настройки пользователя'
        verbose_name_plural = 'настройки пользователей'

    def __str__(self):
        return self.user.__str__()