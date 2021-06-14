from datetime import timedelta
from decimal import Decimal
from time import sleep

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Test
from LMS_API.serializers import TestSerializer



class TestApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test/'

        self.client = APIClient()
        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            start=timezone.now() + timedelta(milliseconds=50),
            end=timezone.now() + timedelta(days=1),
            duration=timedelta(minutes=1)
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

        response = self.client.options(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, PATCH, DELETE, HEAD, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''
        response = self.client.post(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})


class TestRetrieveApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test/'

        self.client = APIClient()
        self.user_subscriber = User.objects.create(username='subscriber', email='user2@example.com')
        self.user_not_subscriber = User.objects.create(username='not subscriber', email='user1@example.com')

        self.token_subscriber = Token.objects.create(user=self.user_subscriber)
        self.token_not_subscriber = Token.objects.create(user=self.user_not_subscriber)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            start=timezone.now() + timedelta(milliseconds=50),
            end=timezone.now() + timedelta(days=1),
            duration=timedelta(minutes=1)
        )

        self.course.students.add(self.user_subscriber)

    def test_GET_invalid_pk(self):
        """"""
        response = self.client.get(f'{self.URL}-1/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.get(f'{self.URL}{self.test.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_GET_with_authorization_not_subscriber(self):
        '''Тест отображается только тем кто подписан на курс'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        response = self.client.get(f'{self.URL}{self.test.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        response = self.client.get(f'{self.URL}{self.test.id}/')
        serializer_data = TestSerializer(self.test, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)

# + (number_of_attempts обязательно при default=1)
class TestCreateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')

        self.token_owner = Token.objects.create(user=self.user_owner)
        self.token_not_owner = Token.objects.create(user=self.user_not_owner)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')

        self.course.owners.add(self.user_owner)


    def test_POST_with_authorization_invalid_pk(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {'course_element': 'abc'}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Страница не найдена."
        })

    def test_POST_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        data = {}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_POST_with_authorization_empty(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "course_element": "Обязательное поле."
        })

    def test_POST_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = { 'course_element': self.course_element.id }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_with_authorization_owner_empty_data(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = { 'course_element': self.course_element.id }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'title': ['Обязательное поле.'],
            'test_type': ['Обязательное поле.'],
            'mark_outer': ['Обязательное поле.'],
            'start': ['Обязательное поле.'],
            'end': ['Обязательное поле.'],
            'duration': ['Обязательное поле.'],
            'questions': ['Обязательное поле.'],
        })

    def test_POST_with_authorization_owner_invalid_test(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'course_element': self.course_element.id,
            'title': 'новый тест',
            'test_type': 'abc',
            'mark_outer': 's',
            'start': '2020-01-01 00:00:00',
            'end': '2020-01-01 00:00:00',
            'duration': '00:00:00',
            'questions': 'abc',
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'duration': ['Убедитесь, что это значение больше либо равно 0:00:01.'],
            'end': ['value < timezone.now() --> datetime must be in the future'],
            'mark_outer': ['Требуется численное значение.'],
            'questions': ['Требуется тип данных массив.'],
            'start': ['value < timezone.now() --> datetime must be in the future'],
            'test_type': ['Значения abc нет среди допустимых вариантов.'],
        })

    def test_POST_with_authorization_owner_invalid_questions(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'course_element': self.course_element.id,
            'title': 'новый тест',
            'test_type': 'one',
            'mark_outer': '100',
            'number_of_attempts': 1, # почему-то обязательно при default=1
            'start': '2030-01-01 00:00:00',
            'end': '2030-02-01 00:00:00',
            'duration': '00:05:00',
            'questions': [
                {
                    'question_text': 'менять формат answer_true?',
                    'max_mark': Decimal(10),
                    'answer_type': 'free',
                    'answer_values': [],
                    'answer_true': ''
                },
                {
                    'question_text': 'менять формат answer_true?',
                    'max_mark': Decimal(10),
                    'answer_type': 'one',
                    'answer_values': ['да', 'нет', 'не знаю'],
                    'answer_true': '0 2'
                }
            ],
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'вопрос 0': {'answer_true': ['Обязательное поле.']},
            'вопрос 1': {'answer_true': ['incorrect']},
        })

    def test_POST_with_authorization_owner_correct(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'course_element': self.course_element.id,
            'title': 'новый тест',
            'test_type': 'one',
            'mark_outer': '100',
            'number_of_attempts': 1, # почему-то обязательно при default=1
            'start': '2030-01-01 00:00:00',
            'end': '2030-02-01 00:00:00',
            'duration': '00:05:00',
            'questions': [
                {
                    'question_text': 'менять формат answer_true?',
                    'max_mark': Decimal(10),
                    'answer_type': 'free',
                    'answer_values': [],
                    'answer_true': 'нет'
                },
                {
                    'question_text': 'менять формат answer_true?',
                    'max_mark': Decimal(10),
                    'answer_type': 'one',
                    'answer_values': ['да', 'нет', 'не знаю'],
                    'answer_true': '1'
                }
            ],
        }
        response = self.client.post(self.URL, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # проверить в БД
        self.assertEqual(1, Test.objects.all().count())

        serializer_data = TestSerializer(Test.objects.all().first(), many=False).data
        self.assertEqual(response.data, serializer_data)


class TestDeleteApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')

        self.token_owner = Token.objects.create(user=self.user_owner)
        self.token_not_owner = Token.objects.create(user=self.user_not_owner)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            start=timezone.now() + timedelta(milliseconds=50),
            end=timezone.now() + timedelta(days=1),
            duration=timedelta(minutes=1)
        )

        self.course.owners.add(self.user_owner)

    def test_DELETE_invalid_pk(self):
        """"""
        response = self.client.delete(f'{self.URL}-1/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_DELETE_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.delete(f'{self.URL}{self.test.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_DELETE_with_authorization_not_ownet(self):
        '''Тест отображается только тем кто подписан на курс'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.delete(f'{self.URL}{self.test.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_DELETE_with_authorization_owner_test_not_started(self):
        '''тест не начался. его можно удалить'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        response = self.client.delete(f'{self.URL}{self.test.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

    def test_DELETE_with_authorization_owner_test_started(self):
        '''тест начался. его нельзя удалить'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        sleep(0.050)
        response = self.client.delete(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })


class TestUpdateApiTestCase(APITestCase):
    '''Изменение самого теста без вопросов. API для взаимодействия с вопросами в другом месте'''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')

        self.token_owner = Token.objects.create(user=self.user_owner)
        self.token_not_owner = Token.objects.create(user=self.user_not_owner)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            shuffle=True,
            start=timezone.now() + timedelta(milliseconds=50),
            end=timezone.now() + timedelta(days=1),
            duration=timedelta(minutes=1)
        )

        self.course.owners.add(self.user_owner)

    def test_PATCH_invalid_pk(self):
        """"""
        data = {}
        response = self.client.patch(f'{self.URL}-1/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PATCH_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        data = {}
        response = self.client.patch(f'{self.URL}{self.test.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_PATCH_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {}
        response = self.client.patch(f'{self.URL}{self.test.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PATCH_with_authorization_owner_empty(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {}
        response = self.client.patch(f'{self.URL}{self.test.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "empty request"
        })

    def test_PATCH_with_authorization_owner_test_started(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        sleep(0.050)
        data = {}
        response = self.client.patch(f'{self.URL}{self.test.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PATCH_with_authorization_owner_invalid_fields_validation(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'duration': '00:00:00',
        }
        response = self.client.patch(f'{self.URL}{self.test.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'duration': ['Убедитесь, что это значение больше либо равно 0:00:01.']
        })

    def test_PATCH_with_authorization_owner_invalid_model_validation(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "start": "2030-01-01 12:00:00",
            "end": "2030-01-01 11:00:00",
        }
        response = self.client.patch(f'{self.URL}{self.test.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'duration': ['duration <= end-start'],
            'end': ['start < end']
        })

    def test_PATCH_with_authorization_owner_valid(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "shuffle": False,
        }
        response = self.client.patch(f'{self.URL}{self.test.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # проверить обновлённое значение. загружаем из БД обновлённый объект
        test_updated = Test.objects.get(pk=self.test.pk)

        serializer_data = TestSerializer(self.test, many=False).data
        serializer_data_updated = TestSerializer(test_updated, many=False).data

        self.assertNotEqual(serializer_data, serializer_data_updated)
        self.assertJSONEqual(response.content.decode('utf-8'), serializer_data_updated)