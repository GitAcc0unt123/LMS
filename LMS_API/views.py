import logging
import random
from os import mkdir, rename, path

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework import generics
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser #FileUploadParser
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from LMS.models import (
    Course,
    CourseElement,
    Task,
    TaskAnswer,
    TaskAnswerMark,
    TaskTestExecution,
    Test,
    TestQuestion,
    TestQuestionAnswer,
    TestResult,
    FileStorage,
)
from LMS.forms import (
    TaskAnswerCodeModelForm,
    TaskAnswerMarkModelForm,
    TestCreateModelForm,
    TestResultChangeModelForm,
    TestQuestionCreateModelForm,
)
from LMS_API.serializers import (
    UserDetailSerializer,
    UserDataSerializer,
    CourseStudentsSerializer,
    TaskAnswerSerializer,
    TaskAnswerMarkSerializer,
    TestSerializer,
    TestCreateSerializer,
    TestResultRetrieveSerializer,
    TestResultListSerializer,
    FileStorageShortSerializer,
)
from LMS_API.permissions import (
    CourseOwnerPermission,
    TestResultCompletePermission,
    TestResultEvaluatePermission,
    DeleteFilePermission,

    #TIMEOUT_TASK_AUTOMATIC_Permission, # во время тестов не ставить
    #TIMEOUT_TASK_NONAUTOMATIC_Permission,
)

logger = logging.getLogger(__name__)



class CurrentUserView(APIView):
    """Возвращает или изменяет данные пользователя"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Возвращает данные залогиненого пользователя"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status.HTTP_200_OK)

    def patch(self, request):
        """Изменяет данные залогиненого пользователя"""
        serializer = UserDetailSerializer(instance=request.user, data=request.data, partial=True)

        if serializer.is_valid(): #raise_exception=True
            if 0 == len(serializer.validated_data):
                return Response({"detail": "empty request"}, status.HTTP_400_BAD_REQUEST)
            else:
                user_saved = serializer.save()
                return Response(UserDetailSerializer(user_saved).data, status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

class CurrentUserDataView(APIView):
    """Возвращает или изменяет дополнительные данные пользователя"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Возвращает дополнительные данные залогиненого пользователя"""
        serializer = UserDataSerializer(request.user.user_data)
        return Response(serializer.data, status.HTTP_200_OK)

    def patch(self, request):
        """Изменяет дополнительные данные залогиненого пользователя"""
        serializer = UserDataSerializer(instance=request.user.user_data, data=request.data, partial=True)

        if serializer.is_valid():
            if 0 == len(serializer.validated_data):
                return Response({"detail": "empty request"}, status.HTTP_400_BAD_REQUEST)
            else:
                user_data = serializer.save()
                return Response(UserDataSerializer(user_data).data, status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

# todo: дописать для всех случаев и переделать коды возврата)
class CourseSubscribeView(APIView):
    """Подписаться/отписаться от курса"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not (request.user and request.user.is_authenticated):
            return Response({"detail": "Учетные данные не были предоставлены."}, status.HTTP_401_UNAUTHORIZED)

        response_data = {}
        id = request.data.get('course')
        subscribe_state = request.data.get('subscribe')
        key = request.data.get('key')

        if id is None:
            response_data["course"] = "Обязательное поле."
        elif not isinstance(id, int):
            response_data["course"] = "Должно быть типа number."
        elif id < 1:
            response_data["course"] = "Должно быть больше 0."

        if subscribe_state is None:
            response_data["subscribe"] = "Обязательное поле."
        elif not isinstance(subscribe_state, bool):
            response_data["subscribe"] = "Должно быть типа boolean."

        if 0 < len(response_data):
            return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)

        try:
            course = Course.objects.get(id=id)
        except ObjectDoesNotExist:
            response_data = { "course": "Курс не найден." }
            return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)

        if subscribe_state and course.excluded.filter(id=request.user.id).exists():
            response_data = { "detail": "Вам ограничена запись на данный курс." }
            return Response(status=status.HTTP_403_FORBIDDEN, data=response_data)

        try:
            if subscribe_state:
                # случай если уже подписаны
                
                # todo
                if key and key != '' and key == course.key:
                    course.students.add(request.user)
                elif course.groups.filter(pk__in=request.user.groups.all()).exists():
                    course.students.add(request.user)
                elif not course.key and not course.groups.all().exists():
                    course.students.add(request.user)
                else:
                    return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            else:
                # отписаться в любом случае можно
                # случай если уже отписаны
                course.students.remove(request.user)

            response_data = {
                "user": request.user.id,
                "course": course.id,
                "subscribe": subscribe_state
            }
            return Response(status=status.HTTP_200_OK, data=response_data)
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CourseSubscribersView(generics.RetrieveAPIView):
    """Для работы с пользователями подписанными на курс"""
    queryset = Course.objects.all()
    serializer_class = CourseStudentsSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, CourseOwnerPermission]
    #paginate_by = 100

    # возвращает список пользователей подписанных на курс
    #def get(self, request, *args, **kwargs):
    
    def put(self, request, *args, **kwargs):
        """Внести пользователя в чёрный список курса или исключить пользователя из курса"""
        instance = self.get_object() # course
        response_data = {}

        user = request.data.get('user')
        black_list = request.data.get('black_list')

        if user is None:
            response_data ["user"] = "Обязательное поле."
        elif not isinstance(user, int):
            response_data["user"] = "Должно быть типа number."
        elif user < 1:
            response_data["user"] = "Должно быть больше 0."

        if black_list is None:
            response_data["black_list"] = "Обязательное поле."
        elif not isinstance(black_list, bool):
            response_data["black_list"] = "Должно быть типа boolean."

        if 0 < len(response_data):
            return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)

        try:
            user = User.objects.get(id=user)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={ "user": "Пользователь не найден." })

        instance.students.remove(user)
        if black_list:
            instance.excluded.add(user)
        
        return Response(status=status.HTTP_200_OK)

# + (можно оценить если код выполняется)
class TaskAnswerEvaluateView(APIView):
    """поставить оценку за ответ на задание"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]#, CourseOwnerPermission]

    def put(self, request, pk, *args, **kwargs):
        """Поставить оценку за ответ на задание"""
        #task_answer = kwargs['pk']
        #mark = request.data.get('mark')
        #review = request.data.get('review')

        try:
            task_answer = TaskAnswer.objects.get(pk=pk)
        except:
            return Response({ "detail": "Ответ на задание не найден." }, status.HTTP_404_NOT_FOUND)

        if not task_answer.task.course_element.course.owners.filter(pk=request.user.pk).exists():
            return Response({"detail": "У вас недостаточно прав для выполнения данного действия."}, status.HTTP_403_FORBIDDEN)

        task_answer_mark = task_answer.get_TaskAnswerMark()
        serializer = TaskAnswerMarkSerializer(instance=task_answer_mark, data=request.data) # partial=True
        serializer.initial_data['teacher'] = request.user.pk
        serializer.initial_data['task_answer'] = task_answer.pk
        serializer.is_valid(raise_exception=True)

        # если partial=True
        #if len(serializer.validated_data) == 2:
        #    return Response({"detail": "empty mark and review"}, status.HTTP_400_BAD_REQUEST)

        # clean() модели
        form = TaskAnswerMarkModelForm(serializer.initial_data, instance=task_answer_mark) # python 3.9
        if not form.is_valid():
            return Response(form.errors, status.HTTP_400_BAD_REQUEST)

        form.save()
        return Response(form.data, status.HTTP_200_OK)


# todo: поменять формат получаемого answer_true?)
class TestCreateView(APIView):
    """
    API для создания теста
    {
        'title': string,
        'description': string,
        'mark_outer': Decimal,
        'number_of_attempts': number,
        'shuffle': boolean,
        'test_type': string,
        'duration': timedelta,
        'course_element': id,
        'start': '2020-01-01 00:00:00',
        'end': 2020-01-01 00:00:00',
        'questions': [
            'question_text': string,
            'max_mark': Decimal,
            'answer_type': string,
            'answer_values': [string],
            'answer_true': string  // переделать на [string]?
        ]
    }
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = [permissions.IsAuthenticated, CourseOwnerPermission]

    def post(self, request, *args, **kwargs):
        # получает инфу для теста и от 1 до 70 вопросов
        if not (request.user and request.user.is_authenticated):
            return Response({"detail": "Учетные данные не были предоставлены."}, status.HTTP_401_UNAUTHORIZED)

        course_element = request.data.get('course_element')
        if not course_element:
            return Response({'course_element':'Обязательное поле.'}, status.HTTP_400_BAD_REQUEST)

        try:
            course_element = CourseElement.objects.get(pk=course_element)
        except:
            return Response({'detail':'Страница не найдена.'}, status.HTTP_400_BAD_REQUEST)

        if not course_element.course.owners.filter(pk=request.user.pk).exists():
            return Response({"detail": "У вас недостаточно прав для выполнения данного действия."}, status.HTTP_403_FORBIDDEN)

        # пустой тест заходит в clean() модели
        field_errors = {}
        serializer = TestCreateSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            field_errors = field_errors | dict(serializer.errors) # python 3.9

        # проверка вопросов
        questions = request.data.get('questions')
        if not questions:
            field_errors['questions'] = ['Обязательное поле.']
        elif type(questions) != list:
            field_errors['questions'] = ['Требуется тип данных массив.']
        elif len(questions) == 0 or 70 < len(questions):
            field_errors['questions'] = ['Должно быть от 1 до 70 вопросов']

        if 0 < len(field_errors):
            return Response(field_errors, status.HTTP_400_BAD_REQUEST)

        # проверяем clean() модели Test
        test_form = TestCreateModelForm(data=serializer.validated_data) #data=request.data

        if not test_form.is_valid():
            return Response(test_form.errors, status=status.HTTP_400_BAD_REQUEST)
        test = test_form.save()

        # обрабатываем вопросы
        for question in questions:
            question['test'] = test.pk

            # преобразуем к формату хранения в базе данных
            if 'answer_values' in question and type(question['answer_values']) is list:
                question['answer_values'] = '\n'.join(question['answer_values'])

            #if 'answer_type' in question and question['answer_type'] != 'free' and 'answer_true' in question:
            #    question['answer_true'] = ' '.join(str(x) for x in question['answer_true'])

        # проверяем вопросы по одному с помощью формы
        question_forms = [ TestQuestionCreateModelForm(data=question) for question in questions ]
        response_data = {}
        for i in range(len(question_forms)):
            if not question_forms[i].is_valid():
                response_data[f'вопрос {i}'] = question_forms[i].errors

        # удаляем тест если в вопросах есть ошибки
        if 0 < len(response_data):
            test.delete()
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        questions = TestQuestion.objects.bulk_create(form.save(commit=False) for form in question_forms)

        serializer = TestSerializer(test)
        return Response(serializer.data, status.HTTP_201_CREATED)


class TestResultListView(generics.ListAPIView):
    """список прохождений пользователя за тест (завершённые и активный)"""
    queryset = TestResult.objects.all()
    serializer_class = TestResultListSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = []

    def get(self, request, *args, **kwargs): 
        if not (request.user and request.user.is_authenticated):
            return Response({"detail": "Учетные данные не были предоставлены."}, status.HTTP_401_UNAUTHORIZED)

        test_id = self.request.query_params.get('test_id')
        if test_id is None:
            return Response({"detail": "Required GET param test_id."}, status.HTTP_400_BAD_REQUEST)

        try:
            test = Test.objects.get(pk=test_id)
        except:
            return Response({"test_id": "Страница не найдена."}, status.HTTP_404_NOT_FOUND)

        # проверка прав. через permission?
        if not test.course_element.course.students.filter(pk=request.user.pk).exists():
            return Response({"detail": "У вас недостаточно прав для выполнения данного действия."}, status.HTTP_403_FORBIDDEN)

        queryset = self.get_queryset().filter(test=test_id, user=request.user).order_by('id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# todo: OPTIONS)
class TestResultCompleteView(generics.GenericAPIView):
    """завершить активное прохождение теста"""
    queryset = TestResult.objects.all()

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, TestResultCompletePermission]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object() # Testresult

        instance.end = timezone.now()
        instance.save(update_fields=['end'])

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        serializer = TestResultRetrieveSerializer(instance)
        return Response(serializer.data, status.HTTP_200_OK)

# todo: OPTIONS)
class TestResultEvaluateView(generics.GenericAPIView):
    """оценить вручную завершённое прохождение теста"""
    queryset = TestResult.objects.all()
    serializer_class = TestResultRetrieveSerializer

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, CourseOwnerPermission, TestResultEvaluatePermission]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance, data=request.data, partial=True)
        serializer.initial_data['test'] = instance.test.pk
        serializer.initial_data['user'] = instance.user.pk
        serializer.is_valid(raise_exception=True)

        if 'mark' not in serializer.validated_data:
            return Response({"mark": ["Обязательное поле."]}, status.HTTP_400_BAD_REQUEST)

        # clean() модели
        form = TestResultChangeModelForm(serializer.initial_data, instance=instance) # python 3.9
        if not form.is_valid():
            return Response(form.errors, status.HTTP_400_BAD_REQUEST)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        test_result = form.save()
        serializer_data = TestResultRetrieveSerializer(test_result).data
        return Response(serializer_data, status.HTTP_200_OK)


class TestResultCreateView(APIView):
    """создать прохождение если есть возможность и нет активных прохождений"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    #
    def post(self, request, *args, **kwargs):
        if not (request.user and request.user.is_authenticated):
            return Response({"detail": "Учетные данные не были предоставлены."}, status.HTTP_401_UNAUTHORIZED)

        if type(request.data) != dict:
            return Response({'detail': 'Invalid body type.'}, status.HTTP_400_BAD_REQUEST)

        test_pk = request.data.get('test')
        if not test_pk:
            return Response({'test': 'Обязательное поле.'})

        try:
            test = Test.objects.get(pk=test_pk)
        except:
            return Response({'test':'Страница не найдена.'}, status.HTTP_400_BAD_REQUEST)

        # проверяем что подписан на курс
        if not test.course_element.course.students.filter(pk=request.user.pk).exists():
            return Response({"detail": "У вас недостаточно прав для выполнения данного действия."}, status.HTTP_403_FORBIDDEN)

        # проверяем что тест не завершился, есть попытки и нет активных прохождений
        if timezone.now() < test.start:
            return Response({"detail": "Тестирование не началось."}, status.HTTP_403_FORBIDDEN)

        if test.end < timezone.now():
            return Response({"detail": "Тестирование завершено."}, status.HTTP_403_FORBIDDEN)

        test_results = list(TestResult.objects.filter(test=test, user=request.user))
        if any(not r.is_finished() for r in test_results):
            return Response({"detail": "Есть активное прохождение теста."}, status.HTTP_403_FORBIDDEN)

        if test.number_of_attempts <= len(test_results):
            return Response({"detail": "Закончились попытки."}, status.HTTP_403_FORBIDDEN)

        # можно подловить тайминг, когда проверки выше пройдут, а здесь выскочит исключение?
        # в save() создадутся TestQuestionAnswer
        test_result = TestResult.objects.create(test=test, user=request.user)

        # определяем порядок вопросов в прохождении
        questions = test_result.test.test_questions.all().order_by('id')

        if test.shuffle:
            questions_order = list(range(test.test_questions.count()))
            random.shuffle(questions_order)

            questions_initial = list(questions)
            questions = [questions_initial[i] for i in questions_order]

        # создаём записи под ответы для данного прохождения теста
        test_question_answers = (TestQuestionAnswer(test_result=test_result, test_question=q) for q in questions)
        TestQuestionAnswer.objects.bulk_create(test_question_answers)

        serializer = TestResultListSerializer(test_result, many=False)
        return Response(serializer.data, status.HTTP_201_CREATED)


class UploadFilesCourseElementView(APIView):
    """API для добавления файлов к элементу курса"""
    parser_classes = (MultiPartParser, FormParser)

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = [permissions.IsAuthenticated]#, CourseOwnerPermission]

    def post(self, request, pk, format=None):
        if not (request.user and request.user.is_authenticated):
            return Response({"detail": "Учетные данные не были предоставлены."}, status.HTTP_401_UNAUTHORIZED)

        try:
            course_element = CourseElement.objects.get(pk=pk)
        except:
            return Response({'detail':'Страница не найдена.'}, status.HTTP_400_BAD_REQUEST)

        # проверка прав. через permission?
        if not course_element.course.owners.filter(pk=request.user.pk).exists():
            return Response({"detail": "У вас недостаточно прав для выполнения данного действия."}, status.HTTP_403_FORBIDDEN)

        if 'files' not in request.FILES:
            return Response({"files": "Обязательное поле."}, status.HTTP_400_BAD_REQUEST)

        # проверить загрузку пустых файлов, ограничения на кол-во файлов и их размер
        files = dict(request.FILES)['files']

        datetime = timezone.now()
        newfiles = [ FileStorage.objects.create(
            owner=request.user,
            datetime=datetime,
            file=file,
            course_element=course_element
            ) for file in files ]
        # bulk_create не возвращает pk и не вызывает метод save модели. глянуть .save(commit=False)

        # привязать к нужному element_course
        course_element.files.add(*[file.pk for file in newfiles])

        # вернуть json с созданными объектами
        serializer = FileStorageShortSerializer(course_element.files, many=True)
        return Response(serializer.data, status.HTTP_200_OK)


class UploadFilesTaskView(APIView):
    """API для загрузки файлов в ответ на задание с ручной проверкой"""
    parser_classes = (MultiPartParser, FormParser)

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = [TIMEOUT_TASK_NONAUTOMATIC_Permission]

    def post(self, request, pk, format=None):
        if not (request.user and request.user.is_authenticated):
            return Response({"detail": "Учетные данные не были предоставлены."}, status.HTTP_401_UNAUTHORIZED)

        try:
            task = Task.objects.get(pk=pk)
        except:
            return Response({'detail':'Страница не найдена.'}, status.HTTP_400_BAD_REQUEST)

        # проверка прав. через permission?
        if not task.course_element.course.is_subscriber(request.user):
            return Response({"detail": "У вас недостаточно прав для выполнения данного действия."}, status.HTTP_403_FORBIDDEN)

        if task.execute_answer:
            return Response({"detail": "Задание с автоматической проверкой."}, status.HTTP_403_FORBIDDEN)

        if task.deadline_true < timezone.now():
            return Response({"detail": "deadline"}, status.HTTP_403_FORBIDDEN)

        task_answer = TaskAnswer.objects.filter(task=task, student=request.user).first()
        if task_answer and task_answer.get_TaskAnswerMark():
            return Response({"detail": "Задание оценили."}, status.HTTP_403_FORBIDDEN)

        if 'files' not in request.FILES:
            return Response({"files": "Обязательное поле."}, status.HTTP_400_BAD_REQUEST)

        # проверить загрузку пустых файлов, ограничения на кол-во файлов и их размер с учётом уже имеющихся файлов
        files = dict(request.FILES)['files']

        if all(file.size == 0 for file in files):
            return Response({'detail':'Все файлы пустые.'}, status.HTTP_400_BAD_REQUEST)

        if task.limit_files_count < len(files) or task.limit_files_memory_MB*1024*1024 < sum(f.size for f in files):
            return Response({'detail':'Превышены ограничения на файлы.'}, status.HTTP_400_BAD_REQUEST)

        if task_answer:
            # удалить текущие файлы
            task_answer.files.update(deleted=True)
            task_answer.files.clear()
        else:
            task_answer = TaskAnswer.objects.create(task=task, student=request.user)

        datetime = timezone.now()
        newfiles = [ FileStorage.objects.create(
            owner=request.user,
            datetime=datetime,
            file=file,
            task_answer=task_answer,
            ) for file in files ]
        # bulk_create не возвращает pk и не вызывает метод save модели. глянуть .save(commit=False)

        # привязать к нужному task_answer
        task_answer.files.add(*[file.pk for file in newfiles])

        # вернуть json с созданными объектами
        serializer = TaskAnswerSerializer(task_answer)
        return Response(serializer.data, status.HTTP_200_OK)

# todo: проверки кода и clean() модели Task)
class UploadCodeTaskView(APIView):
    """API для загрузки кода в ответ на задание с автоматической проверкой"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    #permission_classes = [TIMEOUT_TASK_AUTOMATIC_Permission] # ?

    def post(self, request, pk, format=None):
        if not (request.user and request.user.is_authenticated):
            return Response({"detail": "Учетные данные не были предоставлены."}, status.HTTP_401_UNAUTHORIZED)

        try:
            task = Task.objects.get(pk=pk)
        except:
            return Response({'detail':'Страница не найдена.'}, status.HTTP_400_BAD_REQUEST)

        # проверка прав. через permission?
        if not task.course_element.course.is_subscriber(request.user):
            return Response({"detail": "У вас недостаточно прав для выполнения данного действия."}, status.HTTP_403_FORBIDDEN)

        if not task.execute_answer:
            return Response({"detail": "Задание с ручной проверкой."}, status.HTTP_403_FORBIDDEN)

        if task.deadline_true < timezone.now():
            return Response({"detail": "deadline"}, status.HTTP_403_FORBIDDEN)

        taskAnswer = TaskAnswer.objects.filter(task=task, student=request.user).first()
        if taskAnswer and taskAnswer.get_TaskAnswerMark():
            return Response({"detail": "Задание оценили."}, status.HTTP_403_FORBIDDEN)

        if taskAnswer and taskAnswer.is_running:
            return Response({"detail": "Новый код можно загрузить только после выполнения предыдущего."}, status.HTTP_403_FORBIDDEN)

        code = request.data.get('code')
        language = request.data.get('language')

        if taskAnswer:
            taskAnswer.delete()

        #form = TaskAnswerCodeModelForm(instance=taskAnswer, data={
        form = TaskAnswerCodeModelForm(data={
            'task': task.id,
            'student': request.user.id,
            'language': language,
            'code': code,
            'is_running': True
        })

        if not form.is_valid():
            return Response(form.errors, status.HTTP_400_BAD_REQUEST)

        task_answer = form.save()
        #TaskTestExecution.objects.filter(task_answer=taskAnswer).delete()

        #execute_python.delay(taskAnswer.id)  # .run ?
        dir_path = path.join('/test_dir_execute', str(task_answer.id))
        mkdir(dir_path)

        with open(path.join(dir_path, 'code.py'), 'wt') as fout:
            fout.write(task_answer.code)

        for i, test in enumerate(task.task_tests.all().order_by('id')):
            with open(path.join(dir_path, str(i)), 'wt') as fout:
                fout.write(test.input)

        rename(dir_path, dir_path+'+')
        return Response(status.HTTP_200_OK)


class DeleteFileView(generics.DestroyAPIView):
    """API для удаления файлов на сервере"""
    queryset = FileStorage.objects.filter(deleted=False)
    #serializer_class = None

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, DeleteFilePermission]

    def perform_destroy(self, instance):
        instance.deleted = True

        if instance.course_element:
            instance.course_element.files.remove(instance)
            instance.course_element = None
            instance.save(update_fields=["deleted", "course_element"])
        if instance.task_answer:
            task_answer = instance.task_answer

            instance.task_answer.files.remove(instance)
            instance.task_answer = None
            instance.save(update_fields=["deleted", "task_answer"])

            if task_answer.files.count() == 0:
                task_answer.delete()