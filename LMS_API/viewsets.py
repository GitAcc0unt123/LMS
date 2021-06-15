import logging

from rest_framework import status
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
#from rest_framework.filters import OrderingFilter, SearchFilter
#from rest_framework.decorators import action, permission_classes
#from django_filters.rest_framework import DjangoFilterBackend

from LMS.models import (
    Course,
    CourseElement,
    Task,
    TaskTest,
    TaskAnswer,
    Test,
    TestQuestion,
    TestResult,
    TestQuestionAnswer,
    Notification,
    Comment,
)
from LMS.forms import (
    TaskModelForm,
    TaskTestModelForm,
    TestChangeModelForm,
    TestQuestionCreateModelForm,
    TestQuestionAnswerModelForm,
)
from .serializers import (
    CourseRetrieveSerializer,
    CourseUpdateSerializer,
    CourseListSerializer,
    CourseElementSerializer,
    CourseElementCreateSerializer,
    CourseElementUpdateSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
    TaskTestSerializer,
    TaskAnswerSerializer,
    TestSerializer,
    TestQuestionSerializer,
    TestQuestionAnswerRetrieveSerializer,
    TestQuestionAnswerUpdateSerializer,
    NotificationSerializer,
    CommentSerializer,
)
from .permissions import (
    CourseOwnerPermission,
    CourseSubscriberPermission,
    TaskAnswerOwnerPermission,
    TaskAnswerUnmarkedPermission,
    TestBeforeStartPermission,
    TestQuestionPermission,
    TestQuestionAnswerPermission,
    NotificationOwnerPermission,
    CommentOwnerPermission,
    AddCommentPermission,
    CommentTimeoutPermission,
    CommentDailyPermission,
)

logger = logging.getLogger(__name__)


class CourseViewSet(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    """API для курсов"""
    queryset = Course.objects.all().order_by('id')
    #serializer_class = None

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = []

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', self.get_serializer_context())

        if self.action == 'list':
            return CourseListSerializer(*args, **kwargs)
        elif self.action == 'retrieve':
            return CourseRetrieveSerializer(*args, **kwargs)
        elif self.action == 'update':
            return CourseUpdateSerializer(*args, **kwargs)
        elif self.action is None or self.action == 'metadata':
            return CourseRetrieveSerializer()
        else:
            logger.critical(f'CourseViewSet get_serializer unknown action {self.action}')
            raise Exception()

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            prem = []
        elif self.action == 'update':
            prem = [permissions.IsAuthenticated, CourseOwnerPermission]
        elif self.action == 'metadata': # OPTIONS и HEAD (если есть GET)
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'CourseViewSet get_permissions unknown action {self.action}')
            raise Exception()

        return [premission() for premission in prem] + super().get_permissions()

class CourseElementViewSet(mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    '''API для элемента курса'''
    queryset = CourseElement.objects.all()
    #serializer_class = None

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = []

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', self.get_serializer_context())

        if self.action == 'retrieve':
            return CourseElementSerializer(*args, **kwargs)
        elif self.action == 'create':
            return CourseElementCreateSerializer(*args, **kwargs)
        elif self.action == 'update' or self.action == 'partial_update' or self.action == 'destroy':
            return CourseElementUpdateSerializer(*args, **kwargs)
        elif self.action == 'metadata':
            return CourseElementSerializer()
        elif self.action is None: # method not allowed
            return CourseElementSerializer()
        else:
            logger.critical(f'CourseElementViewSet get_serializer unknown action {self.action}')
            raise Exception()

    def get_permissions(self):
        if self.action == 'retrieve':
            prem = []
        elif self.action == 'update' or self.action == 'partial_update' or self.action == 'create' or self.action == 'destroy':
            prem = [permissions.IsAuthenticated, CourseOwnerPermission]
        elif self.action == 'metadata':
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'CourseElementViewSet get_permissions unknown action {self.action}')
            raise Exception()

        return [premission() for premission in prem] + super().get_permissions()

class TaskViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """API для заданий"""
    queryset = Task.objects.all()
    #serializer_class = None

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = []

    def create(self, request, *args, **kwargs):
        # clean() модели
        form = TaskModelForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status.HTTP_400_BAD_REQUEST)

        task = form.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', self.get_serializer_context())

        if self.action == 'retrieve' or self.action == 'create':
            return TaskSerializer(*args, **kwargs)
        elif self.action == 'partial_update' or self.action == 'destroy':
            return TaskUpdateSerializer(*args, **kwargs)
        elif self.action == 'metadata':
            return TaskSerializer()
        elif self.action is None: # method not allowed
            return TaskSerializer()
        else:
            logger.critical(f'TaskViewSet get_serializer unknown action {self.action}')
            raise Exception()

    def get_permissions(self):
        if self.action == 'retrieve':
            prem = [CourseSubscriberPermission]
        elif self.action == 'partial_update' or self.action == 'create' or self.action == 'destroy':
            prem = [permissions.IsAuthenticated, CourseOwnerPermission]
        elif self.action == 'metadata':
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'TaskViewSet get_permissions unknown action {self.action}')
            raise Exception()

        return [premission() for premission in prem] + super().get_permissions()


class TaskTestViewSet(mixins.RetrieveModelMixin,
                      #mixins.UpdateModelMixin,
                      mixins.CreateModelMixin, # при ручном задании должен возвращать код 400
                      mixins.DestroyModelMixin,
                      #mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """API для тестов к заданиям с автоматической проверкой"""
    queryset = TaskTest.objects.all()
    serializer_class = TaskTestSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = [permissions.IsAuthenticated, CourseOwnerPermission]

    def create(self, request, *args, **kwargs):
        # clean() модели
        form = TaskTestModelForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status.HTTP_400_BAD_REQUEST)

        task_test = form.save()
        serializer = self.get_serializer(task_test)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.action == 'retrieve' or self.action == 'destroy' or self.action == 'create':
            prem = [permissions.IsAuthenticated, CourseOwnerPermission]
        elif self.action == 'metadata':
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'TaskTestViewSet get_permissions unknown action {self.action}')
            raise Exception()

        return [premission() for premission in prem] + super().get_permissions()


# ответ на задание создаётся и изменяется через загрузку файлов на сервер
class TaskAnswerViewSet(mixins.RetrieveModelMixin, # получить ответ на задание
                        mixins.DestroyModelMixin, # удалить ответ на задание если нет оценки
                        viewsets.GenericViewSet):
    """API для ответов на задания"""
    queryset = TaskAnswer.objects.all()
    serializer_class = TaskAnswerSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = []

    def perform_destroy(self, instance):
        instance.files.update(deleted=True)
        instance.files.clear()
        instance.delete()

    def get_permissions(self):
        if self.action == 'retrieve':
            prem = [permissions.IsAuthenticated, TaskAnswerOwnerPermission | CourseOwnerPermission]
        elif self.action == 'destroy':
            prem = [permissions.IsAuthenticated, TaskAnswerOwnerPermission, TaskAnswerUnmarkedPermission]
        elif self.action == 'metadata':
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'TaskAnswerViewSet get_permissions unknown action {self.action}')
            raise Exception()

        return [premission() for premission in prem] + super().get_permissions()


class TestViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """API для тестов"""
    queryset = Test.objects.all()
    serializer_class = TestSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = []

    # переделываем patch
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True) # если False она захочет все обязательные поля
        serializer.is_valid(raise_exception=True)

        if len(serializer.validated_data) == 0:
            return Response({"detail": "empty request"}, status.HTTP_400_BAD_REQUEST)

        # clean() модели
        form = TestChangeModelForm(dict(serializer.data) | request.data, instance=instance) # python 3.9
        if form.is_valid():
            form.save()
        else:
            return Response(form.errors, status.HTTP_400_BAD_REQUEST)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(form.data, status.HTTP_200_OK) #serializer.data


    def get_permissions(self):
        if self.action == 'retrieve':
            prem = [permissions.IsAuthenticated, CourseSubscriberPermission|CourseOwnerPermission]
        elif self.action == 'partial_update' or self.action == 'destroy':
            prem = [permissions.IsAuthenticated, CourseOwnerPermission, TestBeforeStartPermission]
        elif self.action == 'metadata':
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'TestViewSet get_permissions unknown action{self.action}')
            raise Exception()

        return [premission() for premission in prem] + super().get_permissions()


class TestQuestionViewSet(mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """API для вопросов теста"""
    queryset = TestQuestion.objects.all()
    serializer_class = TestQuestionSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = []

    def create(self, request, *args, **kwargs):
        # clean() модели
        form = TestQuestionCreateModelForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status.HTTP_400_BAD_REQUEST)

        form.save()
        return Response(form.data, status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.action == 'retrieve':
            prem = [permissions.IsAuthenticated, (CourseSubscriberPermission&TestQuestionPermission)|CourseOwnerPermission]
        elif self.action == 'create' or self.action == 'destroy':
            prem = [permissions.IsAuthenticated, CourseOwnerPermission, TestBeforeStartPermission]
        elif self.action == 'metadata':
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'TestQuestionViewSet get_permissions unknown action {self.action}')
            raise Exception()

        return [premission() for premission in prem] + super().get_permissions()


class TestQuestionAnswerViewSet(mixins.RetrieveModelMixin,
                                mixins.UpdateModelMixin,
                                viewsets.GenericViewSet):
    """API для ответов на вопросы тестов"""
    queryset = TestQuestionAnswer.objects.all()
    #serializer_class = TestQuestionAnswerRetrieveSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = []

    # переделываем patch
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        # clean() модели
        form = TestQuestionAnswerModelForm(request.data, instance=instance)
        if form.is_valid():
            instance = form.save()
        else:
            return Response(form.errors, status.HTTP_400_BAD_REQUEST)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status.HTTP_200_OK)

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', self.get_serializer_context())

        if self.action == 'retrieve':
            return TestQuestionAnswerRetrieveSerializer(*args, **kwargs)
        elif self.action == 'partial_update':
            return TestQuestionAnswerUpdateSerializer(*args, **kwargs)
        elif self.action == 'metadata':
            return TestQuestionAnswerRetrieveSerializer()
        elif self.action is None: # method not allowed
            return TestQuestionAnswerRetrieveSerializer()
        else:
            logger.critical(f'TestQuestionAnswerViewSet get_serializer unknown action {self.action}')
            raise Exception()

    def get_permissions(self):
        if self.action == 'retrieve':
            prem = [permissions.IsAuthenticated, (CourseSubscriberPermission&TestQuestionAnswerPermission)]#|CourseOwnerPermission]
        elif self.action == 'partial_update':
            prem = [permissions.IsAuthenticated, CourseSubscriberPermission&TestQuestionAnswerPermission]
        elif self.action == 'metadata':
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'TestQuestionAnswerViewSet get_permissions unknown action {self.action}')
            raise Exception()

        return [premission() for premission in prem] + super().get_permissions()


class NotificationViewSet(mixins.DestroyModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    """API для уведомлений"""
    queryset = Notification.objects.filter(deleted=False)
    serializer_class = NotificationSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = [permissions.IsAuthenticated, NotificationOwnerPermission]

    # возвращает список уведомлений авторизованного пользователя
    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(user=request.user).order_by('id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # удалить
    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save(update_fields=["deleted"])

    def get_permissions(self):
        if self.action == 'list' or self.action == 'destroy':
            prem = [permissions.IsAuthenticated, NotificationOwnerPermission]
        elif self.action == 'metadata':
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'NotificationViewSet get_permissions unknown action {self.action}')
            raise Exception()

        return [premission() for premission in prem] + super().get_permissions()

# + (примечание. вместо clean() модели Comment проверки делаются в Permission)
class CommentViewSet(mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """API для комментариев"""
    queryset = Comment.objects.filter(deleted=False)
    serializer_class = CommentSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = []

    # создать
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # проверить что комменты включены
        #task = Task.objects.get(pk=serializer.validated_data['task'])
        #if not task.comments_is_on:
        #    return Response({"detail":"Комментарии к задаче выключены."}, status.HTTP_403_FORBIDDEN)
        
        serializer.validated_data['user'] = request.user
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # удалить
    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save(update_fields=["deleted"])

    # возвращает список комментариев авторизованного пользователя
    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(user=request.user).order_by('id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.action == 'create':
            prem = [permissions.IsAuthenticated, CourseSubscriberPermission, AddCommentPermission, CommentTimeoutPermission, CommentDailyPermission]
        elif self.action == 'destroy':
            prem = [permissions.IsAuthenticated, CommentOwnerPermission]
        elif self.action == 'list':
            prem = [permissions.IsAuthenticated]
        elif self.action == 'metadata':
            prem = []
        elif self.action is None: # method not allowed
            prem = []
        else:
            logger.critical(f'CommentViewSet get_permissions unknown action {self.action}')
            raise Exception()

        return super().get_permissions() + [premission() for premission in prem]