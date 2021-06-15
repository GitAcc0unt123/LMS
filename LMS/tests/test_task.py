# при желании можно протестировать clean моделей
# https://docs.djangoproject.com/en/3.2/topics/testing/overview/

from django.test import TestCase

from LMS.models import Course, CourseElement, Task

class TaskTestCase(TestCase):
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.course = Course.objects.create(title="курс")
        self.course_element = CourseElement.objects.create(course=self.course, title="элемент курса")

    #def test_1(self):
    #    """"""
     #   pass