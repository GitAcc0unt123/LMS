from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement


class CourseElementApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course-element/'

        self.client = APIClient()
        self.course = Course.objects.create(title='курс 1')
        self.course_element = CourseElement.objects.create(course=self.course, title="элемент курса 1")

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

        response = self.client.options(f'{self.URL}{self.course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, PUT, DELETE, HEAD, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''

        response = self.client.post(f'{self.URL}{self.course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})


class CourseElementRetrieveApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course-element/'
        self.client = APIClient()
        self.course = Course.objects.create(title='курс 1')
        self.course_element = CourseElement.objects.create(course=self.course, title="элемент курса 1")


    def test_invalid_pk(self):
        ''''''
        response = self.client.get(f'{self.URL}-1/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_pk2(self):
        ''''''
        response = self.client.get(f'{self.URL}abc/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_pk3(self):
        ''''''
        response = self.client.get(f'{self.URL}100/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_without_authorization(self):
        ''''''
        response = self.client.get(f'{self.URL}{self.course_element.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "id": self.course_element.id,
            "course": self.course.id,
            "title": 'элемент курса 1',
            "description": '',
            "files": [],
            "tasks": [],
            "tests": []
        })


class CourseElementDestroyApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course-element/'

        self.client = APIClient()
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.token_not_owner = Token.objects.create(user=self.user_not_owner)
        self.token_owner = Token.objects.create(user=self.user_owner)

        self.course = Course.objects.create(title="курс 1")
        self.course_element = CourseElement.objects.create(course=self.course, title="элемент курса 1")

        self.course.owners.add(self.user_owner)


    def test_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = f'{self.URL}{self.course_element.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        url = f'{self.URL}{self.course_element.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'У вас недостаточно прав для выполнения данного действия.'
        })

    def test_with_authorization_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        url = f'{self.URL}{self.course_element.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

        self.assertEqual(0, CourseElement.objects.all().count())

# todo: invalid заменить на код 400?)
class CourseElementCreateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course-element/'

        self.client = APIClient()
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.token_not_owner = Token.objects.create(user=self.user_not_owner)
        self.token_owner = Token.objects.create(user=self.user_owner)

        self.course = Course.objects.create(title="курс 1")
        self.course.owners.add(self.user_owner)

    def test_POST_without_authorization(self):
        """"""
        self.client.credentials()

        data = {}
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_POST_authorization_not_owner(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_authorization_owner_empty(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'detail': 'У вас недостаточно прав для выполнения данного действия.'
        })

    def test_POST_authorization_owner_invalid(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "course": self.course.id+999,
            "title": "элемент курса",
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # заменить на 400?
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'detail': 'У вас недостаточно прав для выполнения данного действия.'
        })

    def test_POST_authorization_owner_invalid2(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "course": "abc",
            "title": "элемент курса",
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # заменить на 400?
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'detail': 'У вас недостаточно прав для выполнения данного действия.'
        })

    def test_POST_authorization_owner_invalid3(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "course": self.course.id,
            "title": True,
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'title': ['Not a valid string.']
        })

    def test_POST_authorization_owner_valid(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            "course": self.course.id,
            "title": "элемент курса",
        }
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "id": 1,
            "course": self.course.id,
            "title": 'элемент курса',
            "description": '',
        })


class CourseElementUpdateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course-element/'

        self.client = APIClient()
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.token_not_owner = Token.objects.create(user=self.user_not_owner)
        self.token_owner = Token.objects.create(user=self.user_owner)

        self.course = Course.objects.create(title="курс 1")
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.course.owners.add(self.user_owner)
    
    def test_PUT_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials
        
        data = {'title':'новый заголовок'}
        response = self.client.put(f'{self.URL}{self.course_element.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_PUT_with_authorization_not_owner(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {'title':'новый заголовок'}
        response = self.client.put(f'{self.URL}{self.course_element.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PUT_with_authorization_owner_empty(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {}
        response = self.client.put(f'{self.URL}{self.course_element.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "title": ["Обязательное поле."]
        })

    def test_PUT_with_authorization_owner_invalid(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {'title': True}
        response = self.client.put(f'{self.URL}{self.course_element.id}/', data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "title": ['Not a valid string.']
        })

    def test_PUT_with_authorization_owner_valid(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {'title': 'новый заголовок'}
        response = self.client.put(f'{self.URL}{self.course_element.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "id": self.course_element.id,
            "title": "новый заголовок",
            "description": "",
        })