from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course
from LMS_API.serializers import CourseRetrieveSerializer

# создание/удаление курсов только через админку


class CourseApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course/'

        self.client = APIClient()
        self.course = Course.objects.create(title="курс 1")

    
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

        response = self.client.options(f'{self.URL}{self.course.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, PUT, HEAD, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''

        response = self.client.post(f'{self.URL}{self.course.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.course.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})

        response = self.client.delete(f'{self.URL}{self.course.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"DELETE\" не разрешен.'})


class CourseListApiTestCase(APITestCase):
    ''''''
    def test_OPTIONS(self):
        '''допустимые методы'''

        response = self.client.options('/api-lms/course/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, HEAD, OPTIONS')

    def test_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        course1 = Course.objects.create(title='курс 1')
        course2 = Course.objects.create(title='курс 2', description='описание курса')
        course3 = Course.objects.create(title='курс 3', description='описание курса')

        response = self.client.get('/api-lms/course/')
        expected_data = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": course1.id,
                    "title": "курс 1"
                },
                {
                    "id": course2.id,
                    "title": "курс 2"
                },
                {
                    "id": course3.id,
                    "title": "курс 3"
                },
            ]
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), expected_data)


class CourseRetrieveApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course/'

        self.client = APIClient()
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.token_not_owner = Token.objects.create(user=self.user_not_owner)
        self.token_owner = Token.objects.create(user=self.user_owner)

        self.course = Course.objects.create(title="курс 1")
        self.course.owners.add(self.user_owner)


    def test_invalid_pk(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = '/api-lms/course/-1/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_pk2(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = '/api-lms/course/abc/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_pk3(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = '/api-lms/course/100/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = f'{self.URL}{self.course.id}/'
        response = self.client.get(url)
        serializer_data = CourseRetrieveSerializer(self.course, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)

    def test_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        url = f'{self.URL}{self.course.id}/'
        response = self.client.get(url)
        serializer_data = CourseRetrieveSerializer(self.course, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)

    def test_with_authorization_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        url = f'{self.URL}{self.course.id}/'
        response = self.client.get(url)
        serializer_data = CourseRetrieveSerializer(self.course, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)


class CourseUpdateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course/'
        self.client = APIClient()
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.token_not_owner = Token.objects.create(user=self.user_not_owner)
        self.token_owner = Token.objects.create(user=self.user_owner)

        self.course = Course.objects.create(title="курс 1")
        self.course.owners.add(self.user_owner)

    def test_PUT_AnonymousUser(self):
        '''method PUT with AnonymousUser'''
        self.client.credentials() # unset any existing credentials

        data = {'title':'новый заголовок'}
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_PUT_Not_Owner(self):
        """авторизован. нет прав"""

        #self.client.force_login(user=self.user1)
        #response = self.client.put(f'{self.URL}{self.course1.id}/', data=data, format='json', HTTP_AUTHORIZATION=self.token1)
        #response = self.client.put(f'{self.URL}{self.course1.id}/', data=data, format='json', headers={'Authorization': f'Token {self.token}'})

        # obtain a CSRF token
        #response = self.client.get('/login/')
        #csrftoken = response.cookies['csrftoken']

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {'title':'новый заголовок'}
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PUT_Owner_Empty(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {}
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "title": [
                "Обязательное поле."
            ]
        })

    def test_PUT_Owner_Incorrect(self):
        '''авторизован. есть права. некорректно'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {'title': 'new title', 'key': '123'}
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "key": [
                "Введите правильное значение."
            ]
        })

    def test_PUT_Owner_Correct(self):
        '''авторизован. есть права. корректно'''

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)
        data = {'title':'новый заголовок'}
        response = self.client.put(f'{self.URL}{self.course.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "id": self.course.id,
            "title": "новый заголовок",
            "description": "",
            "key": None
        })