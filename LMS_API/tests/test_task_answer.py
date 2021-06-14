from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Task, TaskAnswer, TaskAnswerMark, FileStorage
from LMS_API.serializers import TaskAnswerSerializer


class TaskAnswerApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-answer/'
        self.client = APIClient()

        self.user_owner = User.objects.create(username='owner', email='user2@example.com')
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

        self.course.students.add(self.user_owner)

        # загрузили файл в ответ на задание
        file_content = ContentFile('A string with the file content')
        self.file_task_answer = FileStorage.objects.create(owner=self.user_owner, file=file_content, filename='filename')
        self.task_answer = TaskAnswer.objects.create(task=self.task, student=self.user_owner)
        self.task_answer.files.add(self.file_task_answer.id)

        self.file_task_answer.task_answer = self.task_answer
        self.file_task_answer.save()


    def test_OPTIONS(self):
        '''допустимые методы'''

        response = self.client.options(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.has_header('Allow'))

    def test_NOT_ALOWED(self):
        '''методы не разрешены'''

        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.patch(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.head(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_OPTIONS_PK(self):
        '''допустимые методы'''

        response = self.client.options(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, DELETE, HEAD, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''

        response = self.client.post(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})



class TaskAnswerRetrieveApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-answer/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')

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

        self.course.students.add(self.user_owner)

        # загрузили файл в ответ на задание
        file_content = ContentFile('A string with the file content')
        self.file_task_answer = FileStorage.objects.create(owner=self.user_owner, file=file_content, filename='filename')
        self.task_answer = TaskAnswer.objects.create(task=self.task, student=self.user_owner)
        self.task_answer.files.add(self.file_task_answer.id)

        self.file_task_answer.task_answer = self.task_answer
        self.file_task_answer.save()


    def test_GET_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.get(f'{self.URL}{self.task_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_GET_with_authorization_invalid_pk(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.get(f'{self.URL}-1/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Страница не найдена."
        })

    def test_GET_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.get(f'{self.URL}{self.task_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        response = self.client.get(f'{self.URL}{self.task_answer.id}/')
        serializer_data = TaskAnswerSerializer(self.task_answer, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)

    def test_GET_with_authorization_teacher(self):
        ''''''
        self.course.owners.add(self.user_not_owner)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.get(f'{self.URL}{self.task_answer.id}/')
        serializer_data = TaskAnswerSerializer(self.task_answer, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)


class TaskAnswerDestroyApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-answer/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')

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

        self.course.students.add(self.user_owner)

        # загрузили файл в ответ на задание
        file_content = ContentFile('A string with the file content')
        self.file_task_answer = FileStorage.objects.create(owner=self.user_owner, file=file_content, filename='filename')
        self.task_answer = TaskAnswer.objects.create(task=self.task, student=self.user_owner)
        self.task_answer.files.add(self.file_task_answer.id)

        self.file_task_answer.task_answer = self.task_answer
        self.file_task_answer.save()


    def test_DELETE_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.delete(f'{self.URL}{self.task_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_DELETE_with_authorization_invalid_pk(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.delete(f'{self.URL}-1/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Страница не найдена."
        })

    def test_DELETE_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.delete(f'{self.URL}{self.task_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_DELETE_with_authorization_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        response = self.client.delete(f'{self.URL}{self.task_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

    def test_DELETE_with_authorization_owner_marked(self):
        '''нельзя удалить если ответ на задание оценили'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        # ставим оценку за ответ
        self.course.owners.add(self.user_not_owner)
        task_answer_mark = TaskAnswerMark.objects.create(
            task_answer=self.task_answer,
            teacher=self.user_not_owner,
            mark=Decimal(0)
        )

        response = self.client.delete(f'{self.URL}{self.task_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })