from datetime import timedelta
from decimal import Decimal
from time import sleep

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Task, TaskAnswer, TaskAnswerMark

# todo: check code и clean() модели Task)
class TaskUploadCodeApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-upload-code/'

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
            execute_answer=True,
            deadline_visible=timezone.now() + timedelta(milliseconds=50),
            deadline_true=timezone.now() + timedelta(milliseconds=50),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.course.owners.add(self.user_teacher)
        self.course.students.add(self.user_subscriber)


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
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_with_authorization_invalid_pk(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        url = f'{self.URL}-1/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization_not_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'У вас недостаточно прав для выполнения данного действия.'
        })

    def test_with_authorization_exec_OFF(self):
        '''задание с ручной проверкой'''
        task_exec_OFF = Task.objects.create(
            course_element=self.course_element,
            title='задача с ручной проверкой',
            execute_answer=False,
            deadline_visible=timezone.now() + timedelta(milliseconds=100),
            deadline_true=timezone.now() + timedelta(milliseconds=100),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        url = f'{self.URL}{task_exec_OFF.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'Задание с ручной проверкой.'
        })

    def test_with_authorization_subscriber_deadline(self):
        '''дедлайн задачи прошёл'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        sleep(0.050)
        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "deadline"
        })

    def test_with_authorization_subscriber_evaluated(self):
        '''ответ на задание оценили'''
        # ответили на задание
        task_answer = TaskAnswer.objects.create(
            task=self.task,
            student=self.user_subscriber,
            code="print()",
            language="1",
            is_running=False,
        )

        # поставили оценку
        TaskAnswerMark.objects.create(
            task_answer=task_answer,
            teacher=self.user_teacher,
            mark=Decimal(5)
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'Задание оценили.'
        })

    def test_with_authorization_subscriber_running(self):
        '''код исполняется'''
        # ответили на задание
        task_answer = TaskAnswer.objects.create(
            task=self.task,
            student=self.user_subscriber,
            code="print()",
            language="1",
            is_running=True,
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'detail': 'Новый код можно загрузить только после выполнения предыдущего.'
        })

    def test_with_authorization_subscriber_empty(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            #"language": ["Обязательное поле."],
            "code": ["Обязательное поле."]
        })

    # todo
    def test_with_authorization_subscriber_invalid_type(self):
        ''''''
        return
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = { 
            "code": 1,
            "language": True
        }
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'language': ['Выберите корректный вариант. True нет среди допустимых значений.'],
            'code': [],
        })

    # todo
    def test_with_authorization_subscriber_invalid_code(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = { 
            "language": "1",
            "code": "import math\nfrom os import path\n\nprint(open('file.txt', 'rt').read())"
        }
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "code": ['import now allowed', 'this built-in function not allowed'],
        })

    # todo
    def test_with_authorization_subscriber_valid(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = { 
            "language": "1",
            "code": "print(1)"
        }
        url = f'{self.URL}{self.task.id}/'
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)