from django.contrib.auth.models import User, Group

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course


class CourseSubscribeApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course_subscribe/'

        self.client = APIClient()
        self.user = User.objects.create(username='user1', email='user1@example.com')
        self.token = Token.objects.create(user=self.user)

        self.course = Course.objects.create(title="курс 1")

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


    def test_without_authorization(self):
        ''''''
        self.client.credentials()

        response = self.client.post(self.URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization_empty(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        data = {}
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "course": "Обязательное поле.",
            "subscribe": "Обязательное поле."
        })

    def test_with_authorization_format(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        data = {
            'course': str(self.course.id),
            'subscribe': "True"
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "course": "Должно быть типа number.",
            "subscribe": "Должно быть типа boolean."
        })

    def test_with_authorization_incorrect_course(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        data = {
            'course': self.course.id+1,
            'subscribe': True
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "course": "Курс не найден."
        })

    def test_with_authorization_black_list(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # пользователю ограничили доступ к курсу
        self.course.excluded.add(self.user)

        data = {
            'course': self.course.id,
            'subscribe': True,
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Вам ограничена запись на данный курс."
        })

    def test_with_authorization_key(self):
        """запись авторизованного пользователя на курс по ключу"""

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # задали ограничение для записи на курс по ключу
        self.course.key = "1234567"

        data = {
            'course': self.course.id,
            'subscribe': True,
            'key': self.course.key,
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'user': self.user.id,
            'course': self.course.id,
            'subscribe': True,
        })

    def test_with_authorization_group(self):
        """запись авторизованного пользователя на курс через группу"""

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # задали ограничение для записи на курс через группу
        group = Group.objects.create(name='test group')
        group.user_set.add(self.user)
        self.course.groups.add(group)

        data = {
            'course': self.course.id,
            'subscribe': True,
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'user': self.user.id,
            'course': self.course.id,
            'subscribe': True,
        })

    def test_with_authorization_out(self):
        """покинуть курс для авторизованного пользователя"""

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        #
        self.course.students.add(self.user)

        data = {
            'course': self.course.id,
            'subscribe': False,
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'user': self.user.id,
            'course': self.course.id,
            'subscribe': False,
        })