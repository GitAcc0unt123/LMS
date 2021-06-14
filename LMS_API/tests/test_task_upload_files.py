from time import sleep
from datetime import timedelta
from decimal import Decimal
from os import path, remove

from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.conf import settings

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Task, TaskAnswer, TaskAnswerMark, FileStorage
from LMS_API.serializers import TaskAnswerSerializer

# todo: invalid)
class TaskUploadFilesApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-upload-files/'

        self.client = APIClient()
        self.user_not_subscriber = User.objects.create(username='not subscriber', email='user1@example.com')
        self.user_subscriber = User.objects.create(username='subscriber', email='user2@example.com')
        self.user_teacher = User.objects.create(username='teacher', email='user3@example.com')

        self.token_not_subscriber = Token.objects.create(user=self.user_not_subscriber)
        self.token_subscriber = Token.objects.create(user=self.user_subscriber)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='задача',
            execute_answer=False,
            deadline_visible=timezone.now() + timedelta(milliseconds=50),
            deadline_true=timezone.now() + timedelta(milliseconds=50),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
            limit_files_count=3,
            limit_files_memory_MB=1,
        )

        self.course.owners.add(self.user_teacher)
        self.course.students.add(self.user_subscriber)

        self.file = ContentFile('A string with the file content', name='filename')

    def test_OPTIONS(self):
        '''допустимые методы'''

        response = self.client.options(f'{self.URL}{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'POST, OPTIONS')

    def test_NOT_ALOWED(self):
        '''методы не разрешены'''
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.patch(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.head(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_without_authorization_invalid_pk(self):
        ''''''
        data = {}
        url = f'{self.URL}-1/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_with_authorization_invalid_pk(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        url = f'{self.URL}-1/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization_not_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'У вас недостаточно прав для выполнения данного действия.'
        })

    def test_with_authorization_exec_ON(self):
        '''задание с автоматической проверкой'''
        task_exec_ON = Task.objects.create(
            course_element=self.course_element,
            title='задача с автоматической проверкой',
            execute_answer=True,
            deadline_visible=timezone.now() + timedelta(milliseconds=100),
            deadline_true=timezone.now() + timedelta(milliseconds=100),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        url = f'{self.URL}{task_exec_ON.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'Задание с автоматической проверкой.'
        })

    def test_with_authorization_subscriber_deadline(self):
        '''дедлайн задачи прошёл'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        sleep(0.050)
        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "deadline"
        })

    def test_with_authorization_subscriber_evaluated(self):
        '''ответ на задание оценили'''
        # загрузили файл в ответ на задание
        file_task_answer = FileStorage.objects.create(owner=self.user_subscriber, file=self.file, filename='filename')
        # сразу удаляем из файловой системы созданный файл, иначе если тест не пройдёт, то файл останется
        # записи в БД для теста хватит
        remove(path.join(settings.MEDIA_ROOT, str(file_task_answer.file)))

        task_answer = TaskAnswer.objects.create(task=self.task, student=self.user_subscriber)
        task_answer.files.add(file_task_answer.id)

        file_task_answer.task_answer = task_answer
        file_task_answer.save()

        # поставили оценку
        TaskAnswerMark.objects.create(
            task_answer=task_answer,
            teacher=self.user_teacher,
            mark=Decimal(5)
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'Задание оценили.'
        })

    def test_with_authorization_subscriber_empty(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "files": "Обязательное поле."
        })

    def test_with_authorization_subscriber_invalid_format(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = { "files": True }
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "files": "Обязательное поле."
        })

    def test_with_authorization_subscriber_limitations(self):
        '''ограничения на размер и кол-во файлов'''
        file_1MB = ContentFile('abababababababab'*16*16*16*16, name='filename')

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {
            "files": [file_1MB, file_1MB, file_1MB, file_1MB],
        }
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'detail': 'Превышены ограничения на файлы.'
        })

    def test_with_authorization_subscriber_limitations_empty_files(self):
        '''ограничения на размер и кол-во файлов'''
        file_empty = ContentFile('', name='filename')

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {
            "files": file_empty,
        }
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'detail': 'Все файлы пустые.'
        })

    def test_with_authorization_subscriber_limitations_empty_files2(self):
        '''ограничения на размер и кол-во файлов'''
        file_empty = ContentFile('', name='filename')

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {
            "files": [file_empty, file_empty, file_empty],
        }
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'detail': 'Все файлы пустые.'
        })

    def test_with_authorization_subscriber_valid(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {
            "files": self.file,
        }
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # проверяем созданный ответ на задачу
        self.assertEqual(1, TaskAnswer.objects.all().count())

        task_answer = TaskAnswer.objects.first()
        self.assertEqual(1, task_answer.files.all().count())

        serializer_data = TaskAnswerSerializer(task_answer, many=False).data
        self.assertJSONEqual(response.content.decode('utf-8'), serializer_data)

        # удаляем из файловой системы все созданные файлы
        for file_storage in FileStorage.objects.all():
            remove(path.join(settings.MEDIA_ROOT, str(file_storage.file)))

    def test_with_authorization_subscriber_valid_with_empty_files(self):
        ''''''
        file_empty = ContentFile('', name='filename')

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {
            "files": [self.file, file_empty, file_empty],
        }
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # проверяем созданный ответ на задачу
        self.assertEqual(1, TaskAnswer.objects.all().count())

        task_answer = TaskAnswer.objects.first()
        self.assertEqual(3, task_answer.files.all().count())

        serializer_data = TaskAnswerSerializer(task_answer, many=False).data
        self.assertJSONEqual(response.content.decode('utf-8'), serializer_data)

        # удаляем из файловой системы все созданные файлы
        for file_storage in FileStorage.objects.all():
            remove(path.join(settings.MEDIA_ROOT, str(file_storage.file)))