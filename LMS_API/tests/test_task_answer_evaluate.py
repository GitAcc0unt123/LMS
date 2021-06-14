from LMS.forms import TaskAnswerMarkModelForm
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Task, TaskAnswer, TaskAnswerMark, FileStorage
from LMS_API.serializers import TaskAnswerMarkSerializer

# todo: проверить значения после успешного выставления оценки)
class TaskAnswerEvaluateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/task-answer-evaluate/'
        self.client = APIClient()

        self.user_student = User.objects.create(username='student', email='user1@example.com')
        self.user_teacher = User.objects.create(username='teacher', email='user2@example.com')

        self.token_student = Token.objects.create(user=self.user_student)
        self.token_teacher = Token.objects.create(user=self.user_teacher)

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

        self.course.students.add(self.user_student)
        self.course.owners.add(self.user_teacher)

        # загрузили файл в ответ на задание
        file_content = ContentFile('A string with the file content')
        self.file_task_answer = FileStorage.objects.create(owner=self.user_student, file=file_content, filename='filename')
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
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_student.key) # убрать

        response = self.client.options(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'PUT, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_student.key) # убрать

        response = self.client.get(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"GET\" не разрешен.'})

        response = self.client.post(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})

        response = self.client.delete(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"DELETE\" не разрешен.'})

        response = self.client.head(f'{self.URL}{self.task_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"HEAD\" не разрешен.'})


    def test_PUT_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        data = {}
        response = self.client.put(f'{self.URL}{self.task_answer.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })


    def test_PUT_with_authorization_invalid_pk(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {}
        response = self.client.put(f'{self.URL}100/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Ответ на задание не найден."
        })

    def test_PUT_with_authorization_invalid_pk2(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)
        data = {}
        response = self.client.put(f'{self.URL}-1/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PUT_with_authorization_invalid_pk3(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)
        data = {}
        response = self.client.put(f'{self.URL}abc/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_PUT_with_authorization_not_teacher(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_student.key)

        data = {}
        response = self.client.put(f'{self.URL}{self.task_answer.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PUT_with_authorization_teacher_valid(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {'mark': Decimal(5)}
        response = self.client.put(f'{self.URL}{self.task_answer.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, TaskAnswerMark.objects.all().count())

    def test_PUT_with_authorization_teacher_invalid(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {'mark': Decimal(50)}
        response = self.client.put(f'{self.URL}{self.task_answer.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'mark': ['оценка должна быть меньше или равна 10.00']
        })

    def test_PUT_with_authorization_teacher_empty(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {}
        response = self.client.put(f'{self.URL}{self.task_answer.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'mark': ['Обязательное поле.']
        })

    def test_PUT_with_authorization_teacher_change_mark(self):
        ''''''
        mark = TaskAnswerMark.objects.create(
            task_answer=self.task_answer,
            teacher=self.user_teacher,
            mark=Decimal(5),
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {"mark": Decimal(8)}
        response = self.client.put(f'{self.URL}{self.task_answer.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # проверить обновлённое значение. загружаем из БД обновлённый объект
        #mark_updated = TaskAnswerMark.objects.get(pk=mark.pk)

    def test_PUT_with_authorization_teacher_change_mark_empty(self):
        ''''''
        mark = TaskAnswerMark.objects.create(
            task_answer=self.task_answer,
            teacher=self.user_teacher,
            mark=Decimal(5),
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {}
        response = self.client.put(f'{self.URL}{self.task_answer.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'mark': ['Обязательное поле.']
        })