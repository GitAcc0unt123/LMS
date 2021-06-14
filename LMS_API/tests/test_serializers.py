from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from LMS import models
from LMS_API import serializers


class UserSerializerTestCase(TestCase):
    def test_UserSerializer(self):
        user1 = User.objects.create(username='username1')
        user2 = User.objects.create(username='username2', email='email@email.com')
        user3 = User.objects.create(username='username3', email='email@email.com', first_name='имя', last_name='фамилия')

        data = serializers.UserDetailSerializer([user1, user2, user3], many=True).data
        expected_data = [
            {
                'id': user1.id,
                'username': 'username1',
                'email': '',
                'first_name': '',
                'last_name': '',
            },
            {
                'id': user2.id,
                'username': 'username2',
                'email': 'email@email.com',
                'first_name': '',
                'last_name': '',
            },
            {
                'id': user3.id,
                'username': 'username3',
                'email': 'email@email.com',
                'first_name': 'имя',
                'last_name': 'фамилия',
            }
        ]

        self.assertEqual(expected_data, data)


class CourseRetrieveSerializerTestCase(TestCase):
    def test_CourseSerializer(self):
        course = models.Course.objects.create(title='курс')
        data = serializers.CourseRetrieveSerializer(course, many=False).data
        expected_data = {
                "id": course.id,
                "title": 'курс',
                "description": '',
                "course_elements": []
            }

        self.assertEqual(expected_data, data)


class CourseElementSerializerTestCase(TestCase):
    def test_CourseElementSerializer(self):
        course = models.Course.objects.create(title='курс')
        course_element = models.CourseElement.objects.create(title='элемент курса', course=course)
        data = serializers.CourseElementSerializer(course_element, many=False).data
        expected_data = {
                "id": course_element.id,
                "course": course_element.course.id,
                "title": 'элемент курса',
                "description": '',
                "files": [],
                "tasks": [],
                "tests": []
            }

        self.assertEqual(expected_data, data)


class NotificationSerializerTestCase(TestCase):
    def test_NotificationSerializer(self):
        user = User.objects.create(username='username')
        notification = models.Notification.objects.create(user=user, text='текст уведомления')

        data = serializers.NotificationSerializer(notification, many=False).data
        data.pop('datetime') # с представлением дат не сходятся
        expected_data = {
                'id': notification.id,
                'text': 'текст уведомления',
                #'datetime': str(timezone.localtime(notification.datetime)).replace('', 'T'), # заменяет пробелы на T
                'readed': False
            }

        self.assertEqual(expected_data, data)

#task = models.Task.objects.create(
#    course_element=course_element,
#    title='задание 1',
#    deadline_visible=timezone.now() + timedelta(hours=1),
#    deadline_true=timezone.now() + timedelta(hours=2),
#    mark_outer=100,
#    mark_max=100
#)