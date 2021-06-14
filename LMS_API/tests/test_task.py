from datetime import timedelta
from decimal import Decimal
from logging import fatal, setLogRecordFactory

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Task
from LMS_API.serializers import TaskSerializer, TaskUpdateSerializer


class TaskApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task/'
        self.client = APIClient()

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='задача',
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )


    def test_OPTIONS(self):
        '''допустимые методы'''

        response = self.client.options(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'POST, OPTIONS')

    def test_NOT_ALOWED(self):
        '''методы не разрешены'''
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"GET\" не разрешен.'})

        response = self.client.put(self.URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(self.URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})

        response = self.client.delete(self.URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"DELETE\" не разрешен.'})

        response = self.client.head(self.URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"HEAD\" не разрешен.'})

    def test_OPTIONS_PK(self):
        '''допустимые методы'''

        response = self.client.options(f'{self.URL}{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, PATCH, DELETE, HEAD, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''
        response = self.client.post(f'{self.URL}{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})


class TaskRetrieveApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task/'

        self.client = APIClient()
        self.user_subscriber = User.objects.create(username='subscriber', email='user2@example.com')
        self.user_not_subscriber = User.objects.create(username='not subscriber', email='user1@example.com')

        self.token_subscriber = Token.objects.create(user=self.user_subscriber)
        self.token_not_subscriber = Token.objects.create(user=self.user_not_subscriber)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='задача',
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.course.students.add(self.user_subscriber)

    def test_GET_invalid_pk(self):
        """"""
        response = self.client.get(f'{self.URL}-1/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_invalid_pk2(self):
        """"""
        response = self.client.get(f'{self.URL}abc/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_invalid_pk3(self):
        """"""
        response = self.client.get(f'{self.URL}100/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.get(f'{self.URL}{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_GET_with_authorization_not_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        response = self.client.get(f'{self.URL}{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        response = self.client.get(f'{self.URL}{self.task.id}/')
        serializer_data = TaskSerializer(self.task, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)

# todo
class TaskCreateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user1@example.com')
        self.user_not_owner = User.objects.create(username='not owner', email='user2@example.com')

        self.token_owner = Token.objects.create(user=self.user_owner)
        self.token_not_owner = Token.objects.create(user=self.user_not_owner)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')

        self.course.owners.add(self.user_owner)


    def test_POST_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        data = {}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_POST_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_with_authorization_owner_empty(self):
        ''''''
        return
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'course_element': self.course_element.id,
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'deadline_true': ['Обязательное поле.'],
            'deadline_visible': ['Обязательное поле.'],
            'mark_max': ['Обязательное поле.'],
            'mark_outer': ['Обязательное поле.'],
            'title': ['Обязательное поле.'],
            'execute_answer': ['Обязательное поле.'],
        })

    def test_POST_with_authorization_owner_invalid_EXEC_OFF(self):
        ''''''
        return
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'course_element': self.course_element.id,
            'deadline_visible': '2031-01-01 00:00:00',
            'deadline_true': '2030-01-01 00:00:00',
            'mark_max': Decimal(-5),
            'mark_outer': '10',
            'title': '',
            'execute_answer': False,
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            
        })

    def test_POST_with_authorization_owner_invalid_EXEC_ON(self):
        ''''''
        return
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'course_element': self.course_element.id,
            'deadline_visible': '2031-01-01 00:00:00',
            'deadline_true': '2030-01-01 00:00:00',
            'mark_max': Decimal(-5),
            'mark_outer': '10',
            'title': '',
            'execute_answer': True,
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            
        })

    def test_POST_with_authorization_owner_valid_EXEC_OFF(self):
        ''''''
        return
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'course_element': self.course_element.id,
            'deadline_visible': '2030-01-01 00:00:00',
            'deadline_true': '2030-01-02 00:00:00',
            'mark_max': Decimal(5),
            'mark_outer': '10',
            'title': 'задание 1',
            'execute_answer': False,
            'limit_files_count': 4,
            'limit_files_memory_MB': 4,
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # проверить в БД
        self.assertEqual(1, Task.objects.all().count())

        serializer_data = TaskSerializer(Task.objects.all().first(), many=False).data
        self.assertEqual(response.data, serializer_data)

# todo
class TaskUpdateApiTestCase(APITestCase):
    ''''''
    pass


class TaskDestroyApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user1@example.com')
        self.user_not_owner = User.objects.create(username='not owner', email='user2@example.com')

        self.token_owner = Token.objects.create(user=self.user_owner)
        self.token_not_owner = Token.objects.create(user=self.user_not_owner)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='задача',
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.course.owners.add(self.user_owner)


    def test_DELETE_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.delete(f'{self.URL}{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_DELETE_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.delete(f'{self.URL}{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_DELETE_with_authorization_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        response = self.client.delete(f'{self.URL}{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')