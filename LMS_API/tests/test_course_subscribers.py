from django.contrib.auth.models import User, Group

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course

# todo: OPTIONS
class CourseSubscribersApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course_subscribers/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='user_owner', email='user_owner@example.com')
        self.user1 = User.objects.create(username='user1', email='user1@example.com')
        self.user2 = User.objects.create(username='user2', email='user2@example.com')

        self.token_owner = Token.objects.create(user=self.user_owner)
        self.token_not_owner = Token.objects.create(user=self.user1)

        self.course = Course.objects.create(title="курс 1")
        self.course.owners.add(self.user_owner)
        self.course.students.add(self.user1)
        self.course.students.add(self.user2)

    #def test_OPTIONS(self):
    #    '''допустимые методы'''

    #    response = self.client.options(self.URL)
    #    self.assertEqual(response.status_code, status.HTTP_200_OK)
    #    self.assertTrue(response.has_header('Allow'))
    #    self.assertEqual(response['allow'], 'GET, PUT, HEAD, OPTIONS')

    def test_NOT_ALOWED(self):
        """"""
        pass

    def test_OPTIONS_PK(self):
        ''''''
        pass

    def test_NOT_ALOWED_PK(self):
        """"""
        pass


    def test_GET_without_authorization(self):
        ''''''
        self.client.credentials()

        response = self.client.get(f'{self.URL}{self.course.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_GET_with_authorization_not_owner(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.get(f'{self.URL}{self.course.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_owner(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        response = self.client.get(f'{self.URL}{self.course.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "id": self.course.id,
            "students": [
                "user1",
                "user2",
            ]
        })

    def test_PUT_without_authorization(self):
        ''''''
        self.client.credentials()

        data = {}
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_PUT_with_authorization_not_owner(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {}
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PUT_with_authorization_empty(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {}
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "user": "Обязательное поле.",
            "black_list": "Обязательное поле."
        })

    def test_PUT_with_authorization_format(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "user": str(self.user1.id),
            "black_list": str(True)
        }
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "user": "Должно быть типа number.",
            "black_list": "Должно быть типа boolean."
        })

    def test_PUT_with_authorization_invalid_user(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "user": self.user2.id+999,
            "black_list": True
        }
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "user": "Пользователь не найден."
        })

    def test_PUT_with_authorization_black_list_FALSE(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "user": self.user1.id,
            "black_list": False
        }
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b'')

        self.assertFalse(self.course.excluded.filter(pk=self.user1.pk).exists())
        self.assertFalse(self.course.students.filter(pk=self.user1.pk).exists())

    def test_PUT_with_authorization_black_list_TRUE(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "user": self.user1.id,
            "black_list": True
        }
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b'')

        self.assertTrue(self.course.excluded.filter(pk=self.user1.pk).exists())
        self.assertFalse(self.course.students.filter(pk=self.user1.pk).exists())