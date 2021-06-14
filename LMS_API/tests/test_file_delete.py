from decimal import Decimal
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Task, TaskAnswer, TaskAnswerMark, FileStorage


class FileDeleteApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/file-delete/'

        self.client = APIClient()
        self.user_student = User.objects.create(username='not owner', email='user1@example.com')
        self.user_teacher = User.objects.create(username='owner', email='user2@example.com')

        self.token_student = Token.objects.create(user=self.user_student)
        self.token_teacher = Token.objects.create(user=self.user_teacher)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='задача',
            comments_is_on=True,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.course.owners.add(self.user_teacher)
        self.course.students.add(self.user_student)

        # добавили файл к материалам элемента курса
        file_content = ContentFile('A string with the file content')
        self.file_course_element = FileStorage.objects.create(
            owner=self.user_teacher,
            file=file_content,
            filename='filename',
            course_element=self.course_element
        )
        self.course_element.files.add(self.file_course_element.id)

        # загрузили файл в ответ на задание
        file_content2 = ContentFile('A string with the file content')
        self.file_task_answer = FileStorage.objects.create(owner=self.user_student, file=file_content2, filename='filename')
        self.task_answer = TaskAnswer.objects.create(task=self.task, student=self.user_student)
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
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        response = self.client.options(f'{self.URL}{self.file_course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'DELETE, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_student.key)

        response = self.client.get(f'{self.URL}{self.file_course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"GET\" не разрешен.'})

        response = self.client.post(f'{self.URL}{self.file_course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.file_course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.file_course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})

        response = self.client.head(f'{self.URL}{self.file_course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"HEAD\" не разрешен.'})


    def test_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = f'{self.URL}{self.file_course_element.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization_not_owner_COURSE_ELEMENT(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_student.key)

        url = f'{self.URL}{self.file_course_element.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'У вас недостаточно прав для выполнения данного действия.'
        })

        # проверить что файл на месте. загрузка из БД
        file = FileStorage.objects.get(pk=self.file_course_element.pk)
        self.assertFalse(file.deleted)
        self.assertTrue(self.course_element.files.filter(pk=file.pk).exists())

    def test_with_authorization_owner_COURSE_ELEMENT(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        url = f'{self.URL}{self.file_course_element.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

        # проверить что файл помечен как deleted и отвязан от элемента курса. загрузка из БД
        file = FileStorage.objects.get(pk=self.file_course_element.pk)
        self.assertTrue(file.deleted)
        self.assertFalse(self.course_element.files.filter(pk=file.pk).exists())

    def test_with_authorization_not_owner_TASK_ANSWER(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        url = f'{self.URL}{self.file_task_answer.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'У вас недостаточно прав для выполнения данного действия.'
        })

        # проверить что файл на месте. загрузка из БД
        file = FileStorage.objects.get(pk=self.file_task_answer.pk)
        self.assertFalse(file.deleted)
        self.assertTrue(self.task_answer.files.filter(pk=file.pk).exists())

    def test_with_authorization_owner_TASK_ANSWER_not_evaluated(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_student.key)

        url = f'{self.URL}{self.file_task_answer.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

        # проверить что файл помечен как deleted и отвязан от ответа на задание. загрузка из БД
        file = FileStorage.objects.get(pk=self.file_task_answer.pk)
        self.assertTrue(file.deleted)
        self.assertFalse(self.task_answer.files.filter(pk=file.pk).exists())

    def test_with_authorization_owner_TASK_ANSWER_evaluated(self):
        '''ответ на задание оценили. удалить нельзя'''
        TaskAnswerMark.objects.create(
            task_answer=self.task_answer,
            teacher=self.user_teacher,
            mark=Decimal(5)
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_student.key)

        url = f'{self.URL}{self.file_task_answer.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'У вас недостаточно прав для выполнения данного действия.'
        })