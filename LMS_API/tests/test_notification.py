from LMS_API.serializers import NotificationSerializer
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Notification
from LMS_API.serializers import NotificationSerializer


class NotificationApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/notification/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')
        self.notification = Notification.objects.create(user=self.user_owner, text='текст уведомления')


    def test_OPTIONS(self):
        '''допустимые методы'''

        response = self.client.options(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, HEAD, OPTIONS')

    def test_NOT_ALOWED(self):
        '''методы не разрешены'''
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

    def test_OPTIONS_PK(self):
        '''допустимые методы'''

        response = self.client.options(f'{self.URL}{self.notification.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'DELETE, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''

        response = self.client.get(f'{self.URL}{self.notification.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"GET\" не разрешен.'})

        response = self.client.post(f'{self.URL}{self.notification.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.notification.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.notification.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})

        response = self.client.head(f'{self.URL}{self.notification.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"HEAD\" не разрешен.'})


class NotificationListApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/notification/'

        self.client = APIClient()
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.token_not_owner = Token.objects.create(user=self.user_not_owner)
        self.token_owner = Token.objects.create(user=self.user_owner)

        self.notification1 = Notification.objects.create(user=self.user_owner, text='текст уведомления 1')
        self.notification2 = Notification.objects.create(user=self.user_owner, text='текст уведомления 2')
        self.notification_deleted = Notification.objects.create(user=self.user_owner, text='текст уведомления 3')

        # уведомление помечено как удалённое
        self.notification_deleted.deleted = True
        self.notification_deleted.save(update_fields=['deleted'])


    def test_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        response = self.client.get(self.URL)
        serializer_data = NotificationSerializer([self.notification1, self.notification2], many=True).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "count": 2,
            "next": None,
            "previous": None,
            "results": serializer_data
        })


class NotificationDeleteApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""

        self.client = APIClient()
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.token_not_owner = Token.objects.create(user=self.user_not_owner)
        self.token_owner = Token.objects.create(user=self.user_owner)

        self.notification = Notification.objects.create(user=self.user_owner, text='текст уведомления')
        self.notification_deleted = Notification.objects.create(user=self.user_owner, text='текст уведомления 2')

        # уведомление помечено как удалённое
        self.notification_deleted.deleted = True


    def test_invalid_pk_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = '/api-lms/notification/-1/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_invalid_pk_authorization(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        url = '/api-lms/notification/-1/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Страница не найдена."
        })

    def test_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = f'/api-lms/notification/{self.notification.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        url = f'/api-lms/notification/{self.notification.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Это не ваше уведомление."
        })

    def test_with_authorization_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        url = f'/api-lms/notification/{self.notification.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

        # уведомление помечено как удалённое
        # загружаем значение из БД
        self.assertTrue(Notification.objects.get(pk=self.notification.pk).deleted)

    def test_with_authorization_owner_deleted(self):
        '''попытаться удалить комментарий который помечен как удалённый'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        url = f'/api-lms/notification/{self.notification_deleted.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')