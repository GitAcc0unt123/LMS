from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Task, TaskTest


class TaskTestTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-test/'
        self.client = APIClient()

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='task_execute_ON',
            execute_answer=True,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )
        self.task_test = TaskTest.objects.create(task=self.task, input='input', output='output', hidden=True)


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

        response = self.client.options(f'{self.URL}{self.task_test.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, DELETE, HEAD, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''

        response = self.client.post(f'{self.URL}{self.task_test.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.task_test.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.task_test.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})



class TaskTestRetrieveTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-test/'

        self.client = APIClient()
        self.user_not_teacher = User.objects.create(username='not teacher', email='user1@example.com')
        self.user_teacher = User.objects.create(username='teacher', email='user2@example.com')

        self.token_not_teacher = Token.objects.create(user=self.user_not_teacher)
        self.token_teacher = Token.objects.create(user=self.user_teacher)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='task_execute_ON',
            execute_answer=True,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )
        self.task_test = TaskTest.objects.create(task=self.task, input='input', output='output', hidden=True)

        self.course.owners.add(self.user_teacher)


    def test_GET_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.get(f'{self.URL}{self.task_test.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_GET_with_authorization_not_teacher(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_teacher.key)

        response = self.client.get(f'{self.URL}{self.task_test.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_teacher(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        response = self.client.get(f'{self.URL}{self.task_test.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'id': self.task_test.id,
            'task': self.task.id,
            'input': 'input',
            'output': 'output',
            'hidden': True,
        })


class TaskTestCreateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-test/'

        self.client = APIClient()
        self.user_teacher  = User.objects.create(username='teacher', email='user1@example.com')
        self.user_not_teacher  = User.objects.create(username='not teacher', email='user2@example.com')

        self.token_teacher = Token.objects.create(user=self.user_teacher)
        self.token_not_teacher = Token.objects.create(user=self.user_not_teacher)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task_exec_ON = Task.objects.create(
            course_element=self.course_element,
            title='task_exec_ON',
            execute_answer=True,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.task_exec_OFF = Task.objects.create(
            course_element=self.course_element,
            title='task_exec_OFF',
            execute_answer=False,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.course.owners.add(self.user_teacher)


    def test_POST_without_authorization(self):
        """"""
        self.client.credentials()

        data = {}
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_POST_authorization_not_teacher_EXEC_OFF(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_teacher.key)

        data = {
            "task": self.task_exec_OFF.id,
            "input": "input",
            "output": "output",
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_authorization_not_teacher_EXEC_ON(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_teacher.key)

        data = {
            "task": self.task_exec_ON.id,
            "input": "input",
            "output": "output",
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_authorization_teacher_EXEC_OFF(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {
            "task": self.task_exec_OFF.id,
            "input": "input",
            "output": "output",
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_authorization_teacher_EXEC_ON(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {
            "task": self.task_exec_ON.id,
            "input": "input",
            "output": "output",
            "hidden": True
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "id": 1,
            "task": self.task_exec_ON.id,
            "input": "input",
            "output": "output",
            "hidden": True,
        })

    def test_POST_authorization_teacher_EXEC_ON_empty_data(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'detail': 'У вас недостаточно прав для выполнения данного действия.'
        })

    def test_POST_authorization_teacher_EXEC_ON_empty_data2(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = { 
            "task": self.task_exec_ON.id,
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'output': ['Обязательное поле.'],
            'hidden': ['Обязательное поле.'],
        })


class TaskTestDeleteApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-test/'

        self.client = APIClient()
        self.user_not_teacher = User.objects.create(username='not teacher', email='user1@example.com')
        self.user_teacher = User.objects.create(username='teacher', email='user2@example.com')

        self.token_not_teacher = Token.objects.create(user=self.user_not_teacher)
        self.token_teacher = Token.objects.create(user=self.user_teacher)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='task_execute_ON',
            execute_answer=True,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )
        self.task_test = TaskTest.objects.create(task=self.task, input='input', output='output', hidden=True)

        self.course.owners.add(self.user_teacher)


    def test_without_authorization_invalid_pk(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = '/api-lms/task-test/-1/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_authorization_invalid_pk(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_teacher.key)

        url = '/api-lms/task-test/-1/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Страница не найдена."
        })

    def test_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = f'{self.URL}{self.task_test.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization_not_teacher(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_teacher.key)

        url = f'{self.URL}{self.task_test.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_with_authorization_teacher(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        url = f'{self.URL}{self.task_test.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

        self.assertEqual(0, TaskTest.objects.all().count())