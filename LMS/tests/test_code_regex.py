from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.test import TestCase
from django.contrib.auth.models import User

from LMS.models import Course, CourseElement, Task
from LMS.forms import TaskAnswerCodeModelForm

class TaskTestCase(TestCase):
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.course = Course.objects.create(title="курс")
        self.course_element = CourseElement.objects.create(course=self.course, title="элемент курса")
        self.task = Task.objects.create(
            course_element=self.course_element,
            title='title',
            execute_answer=True,
            deadline_visible=timezone.now() + timedelta(hours=1),
            deadline_true=timezone.now() + timedelta(hours=1),
            mark_outer=Decimal(1),
            mark_max=Decimal(1)
        )

        self.student = User.objects.create(username='user1')
        self.course.students.add(self.student)
        
        self.data = {
            'task': self.task.id,
            'student': self.student.id,
            'language': '1',
            'is_running': True
        }

    def test_invalid_from(self):
        """"""
        self.data['code'] = 'from os import path'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['import now allowed']
        })

    def test_invalid_from2(self):
        """"""
        self.data['code'] = 'from os import path as fs'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['import now allowed']
        })

    def test_invalid_from3(self):
        """"""
        self.data['code'] = 'from os import *'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['import now allowed']
        })

    def test_invalid_import(self):
        """"""
        self.data['code'] = 'import os'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['import now allowed']
        })

    def test_invalid_import2(self):
        """"""
        self.data['code'] = 'import os.path'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['import now allowed']
        })

    def test_invalid_import3(self):
        """"""
        self.data['code'] = 'import math, os as fin, random'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['import now allowed']
        })

    def test_invalid_import4(self):
        """"""
        self.data['code'] = 'import math,os as fin, random'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['import now allowed']
        })

    def test_invalid_import5(self):
        """"""
        self.data['code'] = '\nif True:\n\timport math,os as fin, random'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['import now allowed']
        })

    def test_invalid_func(self):
        """"""
        self.data['code'] = "open('1')"
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['this built-in function not allowed']
        })

    def test_invalid_func(self):
        """"""
        self.data['code'] = "[open('1'), 2]"
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'code': ['this built-in function not allowed']
        })

    def test_valid_from(self):
        """"""
        self.data['code'] = 'from math import *'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertTrue(form.is_valid())

    def test_valid_from(self):
        """"""
        self.data['code'] = 'import math'
        form = TaskAnswerCodeModelForm(self.data)
        
        self.assertTrue(form.is_valid())