from datetime import timedelta
from decimal import Decimal
from time import sleep

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Test, TestQuestion, TestResult
from LMS_API.serializers import TestResultListSerializer


class TestResultsApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-result-list/'

        self.user = User.objects.create(username='username', email='user1@example.com')
        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            start=timezone.now() + timedelta(milliseconds=10),
            end=timezone.now() + timedelta(milliseconds=2000),
            duration=timedelta(milliseconds=1000)
        )


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
        self.assertEqual(response['allow'], 'GET, HEAD, OPTIONS')

    def test_NOT_ALOWED(self):
        '''Методы не разрешены'''
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(self.URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(self.URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})

        response = self.client.delete(self.URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"DELETE\" не разрешен.'})


# todo: один assertEqual)
class TestResultListApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-result-list/'

        self.client = APIClient()
        self.user_subscriber = User.objects.create(username='subscriber', email='user1@example.com')
        self.user_subscriber2 = User.objects.create(username='subscriber2', email='user2@example.com')
        self.user_not_subscriber = User.objects.create(username='not subscriber', email='user3@example.com')

        self.token_subscriber = Token.objects.create(user=self.user_subscriber)
        self.token_subscriber2 = Token.objects.create(user=self.user_subscriber2)
        self.token_not_subscriber = Token.objects.create(user=self.user_not_subscriber)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            number_of_attempts=4,
            test_type='one',
            start=timezone.now() + timedelta(milliseconds=10),
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
        self.course.students.add(self.user_subscriber2)

        sleep(0.010)
        self.test_result = TestResult.objects.create(
            test=self.test,
            user=self.user_subscriber,
        )
        self.test_result.complete()
        self.test_result2 = TestResult.objects.create(
            test=self.test,
            user=self.user_subscriber,
        )

        self.test_result3 = TestResult.objects.create(
            test=self.test,
            user=self.user_subscriber2,
        )
        self.test_result3.complete()


    def test_GET_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_GET_with_authorization_invalid_without_param(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Required GET param test_id."
        })

    def test_GET_with_authorization_invalid_param(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        response = self.client.get(f'{self.URL}?test_id=-1')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "test_id": "Страница не найдена."
        })

    def test_GET_with_authorization_not_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        response = self.client.get(f'{self.URL}?test_id={self.test.id}')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        response = self.client.get(f'{self.URL}?test_id={self.test.id}')
        serializer_data = TestResultListSerializer([self.test_result, self.test_result2], many=True).data

        #self.maxDiff = None
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        #self.assertJSONEqual(response.content.decode('utf-8'), {
        #    "count": 2,
        #    "next": None,
        #    "previous": None,
        #    "results": serializer_data
        #})