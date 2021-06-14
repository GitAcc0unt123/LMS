from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Task, Comment
from LMS_API.serializers import CommentSerializer


class CommentApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/comment/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='задача',
            comments_is_on=True,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.comment = Comment.objects.create(user=self.user_owner, task=self.task, text='текст комментария')


    def test_OPTIONS(self):
        '''допустимые методы'''

        response = self.client.options(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, POST, HEAD, OPTIONS')

    def test_NOT_ALOWED(self):
        '''методы не разрешены'''

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

        response = self.client.options(f'{self.URL}{self.comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'DELETE, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''

        response = self.client.get(f'{self.URL}{self.comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"GET\" не разрешен.'})

        response = self.client.post(f'{self.URL}{self.comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})

        response = self.client.head(f'{self.URL}{self.comment.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"HEAD\" не разрешен.'})


class CommentListApiTestCase(APITestCase):
    '''проверить возвращаемый список комментариев авторизованного пользователя'''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/comment/'

        self.client = APIClient()
        self.user1 = User.objects.create(username='user1', email='user1@example.com')
        self.user2 = User.objects.create(username='user2', email='user2@example.com')
        self.user_empty = User.objects.create(username='user3', email='user3@example.com')

        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        self.token_empty = Token.objects.create(user=self.user_empty)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='задача',
            comments_is_on=True,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.course.students.add(self.user1)
        self.course.students.add(self.user2)

        self.comment1 = Comment.objects.create(user=self.user1, task=self.task, text='текст комментария 1')
        self.comment2 = Comment.objects.create(user=self.user1, task=self.task, text='текст комментария 2')
        self.comment3 = Comment.objects.create(user=self.user2, task=self.task, text='текст комментария 3')


    def test_GET_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_GET_with_authorization_user_empty(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_empty.key)

        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "count": 0,
            "next": None,
            "previous": None,
            "results": []
        })

    def test_GET_with_authorization_user1(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)

        response = self.client.get(self.URL)
        serializer_data = CommentSerializer([self.comment1, self.comment2], many=True).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "count": 2,
            "next": None,
            "previous": None,
            "results": serializer_data
        })

    def test_GET_with_authorization_user2(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token2.key)

        response = self.client.get(self.URL)
        serializer_data = CommentSerializer(self.comment3, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [serializer_data]
        })



class CommentCreateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/comment/'

        self.client = APIClient()
        self.user_subscriber  = User.objects.create(username='not owner', email='user1@example.com')
        self.user_not_subscriber  = User.objects.create(username='owner', email='user2@example.com')

        self.token_subscriber = Token.objects.create(user=self.user_subscriber)
        self.token_not_subscriber = Token.objects.create(user=self.user_not_subscriber)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task_comments_ON = Task.objects.create(
            course_element=self.course_element,
            title='комментарии включены',
            comments_is_on=True,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.task_comments_OFF = Task.objects.create(
            course_element=self.course_element,
            title='комментарии выключены',
            comments_is_on=False,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.course.students.add(self.user_subscriber)

    def test_POST_without_authorization(self):
        """"""
        self.client.credentials()

        data = {}
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_POST_authorization_not_subscriber_comments_OFF(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        data = {
            "task": self.task_comments_OFF.id,
            "text": "текст комментария",
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_authorization_not_subscriber_comments_ON(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        data = {
            "task": self.task_comments_ON.id,
            "text": "текст комментария",
        }
        response = self.client.post(self.URL, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_authorization_subscriber_comments_OFF(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {
            "task": self.task_comments_OFF.id,
            "text": "текст комментария"
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_POST_authorization_subscriber_comments_ON(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {
            "task": self.task_comments_ON.id,
            "text": "текст комментария"
        }
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # проверяем созданный комментарий
        self.assertEqual(1, Comment.objects.all().count())

        serializer_data = CommentSerializer(Comment.objects.first(), many=False).data
        self.assertJSONEqual(response.content.decode('utf-8'), serializer_data)

    def test_POST_authorization_empty_data(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        response = self.client.post(self.URL, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'detail': 'У вас недостаточно прав для выполнения данного действия.'
        })


class CommentDeleteApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/comment/'

        self.client = APIClient()
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')

        self.token_not_owner = Token.objects.create(user=self.user_not_owner)
        self.token_owner = Token.objects.create(user=self.user_owner)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='задача',
            comments_is_on=True,
            deadline_visible=timezone.now() + timedelta(days=1),
            deadline_true=timezone.now() + timedelta(days=1),
            mark_outer=Decimal(10),
            mark_max=Decimal(10),
        )

        self.comment = Comment.objects.create(user=self.user_owner, task=self.task, text='текст комментария 1')
        self.comment_deleted = Comment.objects.create(user=self.user_owner, task=self.task, text='текст комментария 2')

        # комментарий помечен как удалённое
        self.comment_deleted.deleted = True


    def test_invalid_pk_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = '/api-lms/comment/-1/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_invalid_pk_authorization(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        url = '/api-lms/comment/-1/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Страница не найдена."
        })

    def test_without_authorization(self):
        ''''''
        self.client.credentials() # unset any existing credentials

        url = f'{self.URL}{self.comment.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        url = f'{self.URL}{self.comment.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Это не ваш комментарий."
        })

    def test_with_authorization_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        url = f'{self.URL}{self.comment.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

        # проверяем что комментарий помечен как удалённое
        # загружаем значение из БД
        self.assertTrue(Comment.objects.get(pk=self.comment.pk).deleted)

    def test_with_authorization_owner_deleted(self):
        '''попытаться удалить комментарий который помечен как удалённый'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        url = f'{self.URL}{self.comment_deleted.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')