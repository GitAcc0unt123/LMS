# https://www.django-rest-framework.org/api-guide/permissions/

from django.utils import timezone
from rest_framework.permissions import BasePermission

import LMS_API.viewsets as viewsets
from LMS.models import (
    Course,
    CourseElement,
    Task,
    TaskAnswer,
    TaskAnswerMark,
    TaskTest,
    Test,
    TestQuestion,
    TestQuestionAnswer,
    TestResult,
)
from django.conf import settings


class CourseOwnerPermission(BasePermission):
    """
    Allows access only to course owners.
    """
    #message = 'Вы не являетесь владельцем учебного курса.'
    def has_permission(self, request, view):
        # создание Task
        if request.method == 'POST' and isinstance(view, viewsets.TaskViewSet):
            course_element = request.data.get('course_element')

            try:
                course_element = CourseElement.objects.get(id=course_element)
            except:
                return False
            return course_element.course.owners.filter(id=request.user.id).exists()

        # создание TaskTest
        # проверить что преподаватель и включена автоматическая проверка у задания
        if request.method == 'POST' and isinstance(view, viewsets.TaskTestViewSet):
            task = request.data.get('task')

            try:
                task = Task.objects.get(id=task)
            except:
                return False
            return task.execute_answer and task.course_element.course.owners.filter(id=request.user.id).exists()

        # создание TestQuestion
        if request.method == 'POST' and isinstance(view, viewsets.TestQuestionViewSet):
            test = request.data.get('test')
            try:
                test = Test.objects.get(id=test)
            except:
                return False
            return test.course_element.course.owners.filter(id=request.user.id).exists()

        # создание CourseElement?
        if request.method == 'POST' and isinstance(view, viewsets.CourseElementViewSet):
            course = request.data.get('course')
            # проверки на корректность course

            try:
                course = Course.objects.get(id=course)
            except:
                return False
            return course.owners.filter(id=request.user.id).exists()

        return True

    # доступ к конкретному объекту модели. вызывается после has_permission
    # view - это viewset который вызвал проверку прав
    # obj - объект к которому просят доступ
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Course):
            return obj.owners.filter(id=request.user.id).exists()
        elif isinstance(obj, CourseElement):
            return obj.course.owners.filter(id=request.user.id).exists()
        elif isinstance(obj, Task):
            return obj.course_element.course.owners.filter(id=request.user.id).exists()
        elif isinstance(obj, TaskAnswer):
            return obj.task.course_element.course.owners.filter(id=request.user.id).exists()
        elif isinstance(obj, TaskTest):
            return obj.task.course_element.course.owners.filter(id=request.user.id).exists()
        elif isinstance(obj, Test):
            return obj.course_element.course.owners.filter(id=request.user.id).exists()
        elif isinstance(obj, TestResult):
            return obj.test.course_element.course.owners.filter(id=request.user.id).exists()
        elif isinstance(obj, TestQuestion):
            return obj.test.course_element.course.owners.filter(id=request.user.id).exists()
        elif isinstance(obj, TestQuestionAnswer):
            return obj.test_question.test.course_element.course.owners.filter(id=request.user.id).exists()
        else:
            return False

class CourseSubscriberPermission(BasePermission):
    """
    Allows access only to course subscribers.
    """
    #message = 'Вы не записаны на курс.'
    def has_permission(self, request, view):
        # создание комментария
        if request.method == 'POST' and isinstance(view, viewsets.CommentViewSet):
            task = request.data.get('task')
            try:
                task = Task.objects.get(id=task)
            except:
                return False

            return task.comments_is_on and task.course_element.course.students.filter(id=request.user.id).exists()

        return True

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Task):
            return obj.course_element.course.students.filter(id=request.user.id).exists()
        elif isinstance(obj, Test):
            return obj.course_element.course.students.filter(id=request.user.id).exists()
        elif isinstance(obj, TestQuestion):
            return obj.test.course_element.course.students.filter(id=request.user.id).exists()
        elif isinstance(obj, TestQuestionAnswer):
            return obj.test_result.test.course_element.course.students.filter(id=request.user.id).exists()
        else:
            return False


class TaskAnswerOwnerPermission(BasePermission):
    """Allows access only to TaskAnswer owner."""
    def has_object_permission(self, request, view, obj):
        return obj.student == request.user

class TaskAnswerUnmarkedPermission(BasePermission):
    """Allows access only to TaskAnswer without mark."""
    def has_object_permission(self, request, view, obj):
        return obj.get_TaskAnswerMark() is None

class TestBeforeStartPermission(BasePermission):
    """
    До начала тестирования тест можно изменить/удалить.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Test):
            return timezone.now() < obj.start
        elif isinstance(obj, TestQuestion):
            return timezone.now() < obj.test.start
        else:
            return False

class TestResultCompletePermission(BasePermission):
    """
    Можно завершить прохождение теста.
    """
    def has_object_permission(self, request, view, obj):
        return bool(
            isinstance(obj, TestResult) and
            obj.user == request.user and
            not obj.is_finished()
        )

class TestResultEvaluatePermission(BasePermission):
    """
    Прохождение теста завершено.
    """
    def has_object_permission(self, request, view, obj):
        return isinstance(obj, TestResult) and obj.is_finished()

class TestQuestionPermission(BasePermission):
    """
    Возможность получить текст вопроса во время прохождения теста.
    """
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, TestQuestion):
            return False

        # считаем что не может быть более одного активного прохождения и id у новых объектов по возрастанию
        test_result = TestResult.objects.filter(test=obj.test, user=request.user).order_by('id').last()
        
        if not test_result or test_result.is_finished():
            return False

        if test_result.test.test_type == 'many':
            # пока тест не завершён доступ без ограничений
            return True
        elif test_result.test.test_type == 'one':
            # ответы на вопросы
            answers = list(test_result.test_result_questions_answers.order_by('id'))

            # obj должен иметь наименьший id среди вопросов на который ещё не ответили
            no_answer = [ x for x in answers if x.answer == '' ]
            return 0 < len(no_answer) and obj.id == no_answer[0].test_question.id
        else:
            raise Exception('неизвестный тип теста')

class TestQuestionAnswerPermission(BasePermission):
    """
    Возможность ответить на вопрос и получить свой ответ во время прохождения теста.
    """
    def has_object_permission(self, request, view, obj):
        if bool(
            not isinstance(obj, TestQuestionAnswer) or
            obj.test_result.user != request.user or
            obj.test_result.is_finished()
        ):
            return False

        if obj.test_result.test.test_type == 'many':
            # пока прохождение не завершено доступ без ограничений
            return True
        elif obj.test_result.test.test_type == 'one':
            answers = list(obj.test_result.test_result_questions_answers.order_by('id'))

            # obj должен иметь наименьший id из тех на которые ещё не ответили
            no_answer = [ x for x in answers if x.answer == '' ]
            return 0 < len(no_answer) and obj.id == no_answer[0].id
        else:
            raise Exception('неизвестный тип теста')


class NotificationOwnerPermission(BasePermission):
    message = 'Это не ваше уведомление.'
    """Allows access only to course owner."""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class CommentOwnerPermission(BasePermission):
    message = 'Это не ваш комментарий.'
    """Allows access only to comment owner."""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class AddCommentPermission(BasePermission):
    """в задаче комментарии включены"""
    def has_permission(self, request, view):
        if request.method == 'POST' and isinstance(view, viewsets.CommentViewSet):
            task = request.data.get('task')
            try:
                task = Task.objects.get(id=task)
            except:
                return False
            return task.comments_is_on


TIMEOUT_COMMENT_DICT = {}
DAILY_COMMENTS_DICT = {}
TIMEOUT_TASK_AUTOMATIC_DICT = {}
TIMEOUT_TASK_NONAUTOMATIC_DICT = {}

class CommentTimeoutPermission(BasePermission):
    """Ограничение на интервалы между комментариями"""
    message = 'Установлены ограничения на интервалы между комментариями.'

    def has_permission(self, request, view):
        pk = request.user.pk
        now = timezone.now()

        if pk not in TIMEOUT_COMMENT_DICT:
            TIMEOUT_COMMENT_DICT[pk] = now
            return True
        elif TIMEOUT_COMMENT_DICT[pk] + settings.TIMEOUT_COMMENT < now:
            TIMEOUT_COMMENT_DICT[pk] = now
            return True
        return False

class CommentDailyPermission(BasePermission):
    """Ограничение на кол-во комментариев"""
    message = 'Установлены ограничения на кол-во комментариев.'

    def has_permission(self, request, view):
        pk = request.user.pk

        if pk not in DAILY_COMMENTS_DICT:
            DAILY_COMMENTS_DICT[pk] = 0

        if DAILY_COMMENTS_DICT[pk] < settings.DAILY_COMMENTS:
            DAILY_COMMENTS_DICT[pk] += 1
            return True
        return False

class TIMEOUT_TASK_AUTOMATIC_Permission(BasePermission):
    """timeout на загрузку кода"""
    message = 'timeout на загрузку кода'

    def has_permission(self, request, view):
        pk = request.user.pk
        now = timezone.now()
        if pk not in TIMEOUT_TASK_AUTOMATIC_DICT:
            TIMEOUT_TASK_AUTOMATIC_DICT[pk] = now
            return True
        elif TIMEOUT_TASK_AUTOMATIC_DICT[pk] + settings.TIMEOUT_TASK_AUTOMATIC < now:
            TIMEOUT_TASK_AUTOMATIC_DICT[pk] = now
            return True
        return False

class TIMEOUT_TASK_NONAUTOMATIC_Permission(BasePermission):
    """timeout на загрузку файлов"""
    message = 'timeout на загрузку файлов'

    def has_permission(self, request, view):
        pk = request.user.pk
        now = timezone.now()
        if pk not in TIMEOUT_TASK_NONAUTOMATIC_DICT:
            TIMEOUT_TASK_NONAUTOMATIC_DICT[pk] = now
            return True
        elif TIMEOUT_TASK_NONAUTOMATIC_DICT[pk] + settings.TIMEOUT_TASK_NONAUTOMATIC < now:
            TIMEOUT_TASK_NONAUTOMATIC_DICT[pk] = now
            return True
        return False

class DeleteFilePermission(BasePermission):
    """"""
    def has_object_permission(self, request, view, obj):
        return bool(
            obj.owner == request.user and obj.task_answer and not obj.task_answer.get_TaskAnswerMark() or # ответ на задание
            obj.course_element and obj.course_element.course.owners.filter(id=request.user.id).exists() or # файл курса
            obj.owner == request.user and not obj.task_answer and not obj.course_element # просто где-то файл валяется
        )