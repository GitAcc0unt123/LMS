from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

# todo: OPTIONS
class CurrentUserApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/current_user/'

        self.client = APIClient()
        self.user = User.objects.create(username='user1', email='user1@example.com')
        self.token = Token.objects.create(user=self.user)

    def test_OPTIONS(self):
        '''допустимые методы'''
        pass

    def test_NOT_ALOWED(self):
        """"""
        pass

    def test_OPTIONS_PK(self):
        '''допустимые методы'''
        pass

    def test_NOT_ALOWED_PK(self):
        """"""
        pass

    def test_GET_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_GET_with_authorization(self):
        """Доступ авторизованного пользователя"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'id': self.user.id,
            'username': 'user1',
            'email': 'user1@example.com',
            'first_name': '',
            'last_name': '',
        })

    def test_PATCH_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.patch(self.URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_PATCH_with_authorization(self):
        """Доступ авторизованного пользователя"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        data = {'first_name':'Вася'}
        response = self.client.patch(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'id': self.user.id,
            'username': 'user1',
            'email': 'user1@example.com',
            'first_name': 'Вася',
            'last_name': '',
        })

    def test_PATCH_with_authorization_empty(self):
        """Доступ авторизованного пользователя"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        data = {}
        response = self.client.patch(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "empty request"
        })

    def test_PATCH_with_authorization_read_only_field(self):
        """Доступ авторизованного пользователя"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        data = {'username':'new username'}
        response = self.client.patch(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "empty request"
        })