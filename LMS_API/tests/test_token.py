from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

# https://www.django-rest-framework.org/api-guide/testing/

# python manage.py test LMS_API

# pip install coverage
# coverage run --source='LMS_API' manage.py test .
# coverage report - вывод в консоль
# coverage html - вывод в html
# см. в выводе строки с файлами views.py, viewsets.py, ...


class TokenApiTestCase(APITestCase):
    '''Получение токена по логину и паролю'''

    def test_OPTIONS(self):
        '''Допустимые методы: POST, OPTIONS'''

        response = self.client.options('/api-auth-token/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'POST, OPTIONS')

    def test_NOT_ALOWED(self):
        '''Методы не разрешены'''
        url = reverse('api-auth-token')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"GET\" не разрешен.'})

        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"HEAD\" не разрешен.'})

        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"DELETE\" не разрешен.'})

    def test_POST_without_data(self):
        '''Required fields username and password'''
        url = reverse('api-auth-token')
        data = {}
        response = self.client.post(url, data=data, format='json') # json=data

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "username":["Обязательное поле."], 
            "password":["Обязательное поле."]
        })

    def test_POST_empty_values(self):
        ''''''
        url = reverse('api-auth-token')
        data = {
            'username':'',
            'password':'',
        }
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "username":["Это поле не может быть пустым."], 
            "password":["Это поле не может быть пустым."]
        })

    def test_POST_incorrect(self):
        ''''''
        user = User.objects.create(username='username1', first_name='first_name', email='test@abc.com')
        user.set_password('password1')
        user.save()

        url = reverse('api-auth-token')
        data = {'username':'username1', 'password':'asdoasd'}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "non_field_errors":["Невозможно войти с предоставленными учетными данными."]
        })

    def test_POST_correct(self):
        ''''''
        user = User.objects.create(username='username1', first_name='first_name', email='test@abc.com')
        user.set_password('password1')
        user.save()

        url = reverse('api-auth-token')
        data = {'username':'username1', 'password':'password1'}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.content.decode('utf-8'))