from decimal import Decimal
from datetime import timedelta
from time import sleep

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Test, TestResult
from LMS_API.serializers import TestResultRetrieveSerializer

# todo: OPTIONS
class TestResultCompleteApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-result-evaluate/'

        self.client = APIClient()
        self.user_teacher  = User.objects.create(username='teacher', email='user1@example.com')
        self.user_not_teacher  = User.objects.create(username='not teacher', email='user2@example.com')

        self.token_teacher = Token.objects.create(user=self.user_teacher)
        self.token_not_teacher = Token.objects.create(user=self.user_not_teacher)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='test',
            mark_outer=Decimal(10),
            test_type='one',
            start=timezone.now() + timedelta(milliseconds=10),
            end=timezone.now() + timedelta(seconds=15),
            duration=timedelta(seconds=10)
        )

        self.course.owners.add(self.user_teacher)
        self.course.students.add(self.user_not_teacher)

        sleep(0.010)
        self.test_result = TestResult.objects.create(
            test=self.test,
            user=self.user_teacher,
            start=timezone.now()
        )
        

    def test_OPTIONS(self):
        '''допустимые методы'''
        response = self.client.options(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.has_header('Allow'))

    def test_NOT_ALOWED(self):
        '''Методы не разрешены'''
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

    #def test_OPTIONS_PK(self):
    #    '''допустимые методы'''
    #    response = self.client.options(f'{self.URL}{self.test_result.id}/')
    #    self.assertEqual(response.status_code, status.HTTP_200_OK)
    #    self.assertTrue(response.has_header('Allow'))
    #    self.assertEqual(response['allow'], 'PATCH, OPTIONS')

    #def test_NOT_ALOWED_PK(self):
    #    '''Методы не разрешены'''


    def test_PATCH_invalid_pk(self):
        """"""
        data = {}
        response = self.client.patch(f'{self.URL}-1/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PATCH_invalid_pk2(self):
        """"""
        data = {}
        response = self.client.patch(f'{self.URL}abc/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PATCH_invalid_pk3(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_teacher.key)
        data = {}
        response = self.client.patch(f'{self.URL}100/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PATCH_without_authorization(self):
        """"""
        self.client.credentials()

        data = {}
        response = self.client.patch(f'{self.URL}{self.test_result.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_PATCH_not_teacher(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_teacher.key)

        data = {}
        response = self.client.patch(f'{self.URL}{self.test_result.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PATCH_teacher_not_finished(self):
        """прохождение теста не завершено"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {}
        response = self.client.patch(f'{self.URL}{self.test_result.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PATCH_teacher_finished_empty(self):
        """прохождение теста завершено"""
        self.test_result.end = timezone.now()
        self.test_result.save(update_fields=['end'])

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {}
        response = self.client.patch(f'{self.URL}{self.test_result.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "mark": ["Обязательное поле."]
        })

    def test_PATCH_teacher_finished_invalid_data(self):
        """прохождение теста завершено"""
        self.test_result.end = timezone.now()
        self.test_result.save(update_fields=['end'])

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {"mark": Decimal(-100)}
        response = self.client.patch(f'{self.URL}{self.test_result.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "mark": ['Убедитесь, что это значение больше либо равно 0.']
        })

    def test_PATCH_teacher_finished_invalid_data2(self):
        """прохождение теста завершено"""
        self.test_result.end = timezone.now()
        self.test_result.save(update_fields=['end'])

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {"mark": "abc"}
        response = self.client.patch(f'{self.URL}{self.test_result.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "mark": ['Требуется численное значение.']
        })

    def test_PATCH_teacher_finished_invalid_data3(self):
        """прохождение теста завершено"""
        self.test_result.end = timezone.now()
        self.test_result.save(update_fields=['end'])

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {"mark": Decimal(999)}
        response = self.client.patch(f'{self.URL}{self.test_result.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "mark": ['оценка должна быть меньше или равна 10.00']
        })

    def test_PATCH_teacher_finished_valid_data(self):
        """прохождение теста завершено"""
        self.test_result.end = timezone.now()
        self.test_result.save(update_fields=['end'])

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {"mark": Decimal(5)}
        response = self.client.patch(f'{self.URL}{self.test_result.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # обновленное значение в БД
        test_result_updated = TestResult.objects.get(pk=self.test_result.pk)

        serializer_data = TestResultRetrieveSerializer(test_result_updated, many=False).data
        self.assertEqual(response.data, serializer_data)