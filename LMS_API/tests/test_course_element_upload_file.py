from os import path, remove

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.conf import settings

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, FileStorage

# todo: сделать ограничения и проверки на материалы курсов?)
class CourseElementUploadFilesApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/course-element-upload-files/'

        self.client = APIClient()
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.token_not_owner = Token.objects.create(user=self.user_not_owner)
        self.token_owner = Token.objects.create(user=self.user_owner)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')

        self.course.owners.add(self.user_owner)

        self.file = ContentFile('A string with the file content', name='filename')

    def test_OPTIONS(self):
        '''допустимые методы'''

        response = self.client.options(f'{self.URL}{self.course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'POST, OPTIONS')

    def test_NOT_ALOWED(self):
        '''методы не разрешены'''
        response = self.client.get(f'{self.URL}{self.course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"GET\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})

        response = self.client.delete(f'{self.URL}{self.course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"DELETE\" не разрешен.'})

        response = self.client.head(f'{self.URL}{self.course_element.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"HEAD\" не разрешен.'})


    def test_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        data = {}
        url = f'{self.URL}{self.course_element.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {}
        url = f'{self.URL}{self.course_element.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": 'У вас недостаточно прав для выполнения данного действия.'
        })

    def test_with_authorization_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = { "files": self.file }
        url = f'{self.URL}{self.course_element.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), [
            {
                "id": 1,
                "filename": "filename"
            }
        ])

        # удаляем из файловой системы созданный файл
        for file_storage in FileStorage.objects.all():
            remove(path.join(settings.MEDIA_ROOT, str(file_storage.file)))

    def test_with_authorization_owner_empty(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {}
        url = f'{self.URL}{self.course_element.id}/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "files": "Обязательное поле."
        })

    def test_with_authorization_invad_pk(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {}
        url = f'{self.URL}-1/'
        response = self.client.post(url, data=data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)