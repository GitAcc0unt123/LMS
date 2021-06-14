from datetime import timedelta
from decimal import Decimal
from random import shuffle
from time import sleep

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Test, TestQuestion, TestResult
from LMS_API.serializers import TestResultListSerializer


class TestResultCreateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-result-create/'

        self.client = APIClient()
        self.user_subscriber = User.objects.create(username='subscriber', email='user1@example.com')
        self.user_not_subscriber = User.objects.create(username='not subscriber', email='user2@example.com')

        self.token_subscriber = Token.objects.create(user=self.user_subscriber)
        self.token_not_subscriber = Token.objects.create(user=self.user_not_subscriber)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            number_of_attempts=1,
            shuffle=True,
            start=timezone.now() + timedelta(milliseconds=25),
            end=timezone.now() + timedelta(milliseconds=2000),
            duration=timedelta(milliseconds=1000)
        )
        self.test_question = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="one",
            answer_values="баг\nфича",
            answer_true="0"
        )

        self.course.students.add(self.user_subscriber)

    
    def test_OPTIONS_PK(self):
        '''допустимые методы'''
        response = self.client.options(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.has_header('Allow'))

    def test_NOT_ALOWED_PK(self):
        '''Методы не разрешены'''
        response = self.client.get(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.post(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.patch(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.head(f'{self.URL}{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_OPTIONS(self):
        '''допустимые методы'''
        response = self.client.options(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'POST, OPTIONS')

    def test_NOT_ALOWED(self):
        '''Методы не разрешены'''
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


    def test_POST_invalid_data(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {'test': -1}
        response = self.client.post(self.URL, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'test': 'Страница не найдена.'
        })

    def test_POST_invalid_data2(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {'test': 999}
        response = self.client.post(self.URL, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'test': 'Страница не найдена.'
        })

    def test_POST_invalid_data3(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {'test': 'abc'}
        response = self.client.post(self.URL, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'test': 'Страница не найдена.'
        })


    def test_POST_without_authorization(self):
        """"""
        self.client.credentials()

        data = {'test': self.test.id}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_POST_not_subscriber_test_not_started(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        data = {'test': self.test.id}
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_not_subscriber_test_started(self):
        """"""
        sleep(0.025)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        data = {'test': self.test.id}
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_subscriber_test_not_started(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {'test': self.test.id}
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Тестирование не началось."
        })

    def test_POST_subscriber_test_started_invalid(self):
        """активное прохождение уже есть"""
        sleep(0.025) # тестирование началось
        TestResult.objects.create(test=self.test, user=self.user_subscriber)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {'test': self.test.id}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Есть активное прохождение теста."
        })

    def test_POST_subscriber_test_started_invalid2(self):
        """закончились попытки"""
        sleep(0.025) # тестирование началось
        test_result = TestResult.objects.create(test=self.test, user=self.user_subscriber)
        test_result.end = timezone.now()
        test_result.save(update_fields=['end'])

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {'test': self.test.id}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Закончились попытки."
        })

    def test_POST_subscriber_test_started_valid(self):
        """прохождение теста активно"""
        sleep(0.025) # тестирование началось
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {'test': self.test.id}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # проверяем значение в БД
        self.assertEqual(1, TestResult.objects.all().count())

        serializer_data = TestResultListSerializer(TestResult.objects.all().first(), many=False).data
        self.assertEqual(response.data, serializer_data)