from datetime import timedelta
from decimal import Decimal
from time import sleep

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Test, TestQuestion, TestResult, TestQuestionAnswer
from LMS_API.serializers import TestQuestionSerializer


class TestQuestionApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question/'

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            start=timezone.now() + timedelta(milliseconds=10),
            end=timezone.now() + timedelta(milliseconds=2000),
            duration=timedelta(milliseconds=1000)
        )
        self.test_question = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="one",
            answer_values="баг\nфича",
            answer_true="0"
        )


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

        response = self.client.options(f'{self.URL}{self.test_question.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, DELETE, HEAD, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''

        response = self.client.post(f'{self.URL}{self.test_question.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.test_question.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.patch(f'{self.URL}{self.test_question.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PATCH\" не разрешен.'})


### MANY ### БЕЗ ДЕЙСТВУЮЩЕЙ ПОПЫТКИ ПРОХОЖДЕНИЯ ТЕСТА (до начала тестирования и во время тестирования)
# считаем что в many прямой и случайные порядки вопросов работают одинаково
class TestQuestion_Retrieve_Many_INACTIVE_ApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question/'

        self.client = APIClient()
        self.user_teacher = User.objects.create(username='teacher', email='user1@example.com')
        self.user_subscriber = User.objects.create(username='subscriber', email='user2@example.com')
        self.user_not_subscriber = User.objects.create(username='not subscriber', email='user3@example.com')

        self.token_teacher = Token.objects.create(user=self.user_teacher)
        self.token_subscriber = Token.objects.create(user=self.user_subscriber)
        self.token_not_subscriber = Token.objects.create(user=self.user_not_subscriber)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')

        self.course.owners.add(self.user_teacher)
        self.course.students.add(self.user_subscriber)

        # создаём тест и вопросы к нему
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='many',
            start=timezone.now() + timedelta(milliseconds=30),
            end=timezone.now() + timedelta(milliseconds=2000),
            duration=timedelta(milliseconds=1000)
        )

        self.test_question = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="one",
            answer_values="баг\nфича",
            answer_true="0"
        )
        self.test_question2 = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="one",
            answer_values="баг\nфича",
            answer_true="1"
        )
        self.test_question3 = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="free",
            answer_values="",
            answer_true="баг"
        )


    def test_GET_invalid_pk(self):
        """"""
        response = self.client.get(f'{self.URL}-1/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_invalid_pk2(self):
        """"""
        response = self.client.get(f'{self.URL}abc/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_invalid_pk3(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        response = self.client.get(f'{self.URL}100/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_without_authorization(self):
        ''''''
        self.client.credentials()

        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

##### ONE не проверяем. считаем что ONE работает точно так же как MANY
    def test_GET_with_authorization_not_subscriber_not_started(self):
        '''до начала теста никому кроме преподавателя нельзя смотреть вопросы'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_subscriber_not_started(self):
        '''до начала теста никому кроме преподавателя нельзя смотреть вопросы'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_teacher_not_started(self):
        '''преподавателю можно смотреть вопросы до начала теста'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'answer_type': 'one',
            'answer_values': 'баг\nфича',
            'max_mark': '1.00',
            'question_text': 'баг или фича?'
        })
 
    def test_GET_with_authorization_not_subscriber_started(self):
        ''''''
        sleep(0.030)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)
        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_subscriber_started(self):
        ''''''
        sleep(0.030)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)
        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_teacher_started(self):
        ''''''
        sleep(0.030)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)
        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'answer_type': 'one',
            'answer_values': 'баг\nфича',
            'max_mark': '1.00',
            'question_text': 'баг или фича?'
        })

    def test_GET_with_authorization_subscriber_started_without_attempt(self):
        '''смотреть вопросы можно только при наличии активного прохождения теста'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        sleep(0.030)
        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })


### MANY ### во время прохождения попытки
class TestQuestion_Retrieve_Many_ACTIVE_ApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question/'

        self.client = APIClient()
        self.user_teacher = User.objects.create(username='teacher', email='user1@example.com')
        self.user_subscriber = User.objects.create(username='subscriber', email='user2@example.com')
        self.user_not_subscriber = User.objects.create(username='not subscriber', email='user3@example.com')

        self.token_teacher = Token.objects.create(user=self.user_teacher)
        self.token_subscriber = Token.objects.create(user=self.user_subscriber)
        self.token_not_subscriber = Token.objects.create(user=self.user_not_subscriber)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='many',
            start=timezone.now() + timedelta(milliseconds=20),
            end=timezone.now() + timedelta(milliseconds=2000),
            duration=timedelta(milliseconds=1000)
        )

        self.test_question = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="one",
            answer_values="баг\nфича",
            answer_true="0"
        )
        self.test_question2 = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="one",
            answer_values="баг\nфича",
            answer_true="1"
        )
        self.test_question3 = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="free",
            answer_values="",
            answer_true="баг"
        )

        self.course.owners.add(self.user_teacher)
        self.course.students.add(self.user_subscriber)

        sleep(0.020)
        self.test_result = TestResult.objects.create(test=self.test, user=self.user_subscriber)

        self.test_question_answer = TestQuestionAnswer.objects.create(
            test_result=self.test_result,
            test_question=self.test_question,
            answer=""
        )
        self.test_question_answer2 = TestQuestionAnswer.objects.create(
            test_result=self.test_result,
            test_question=self.test_question2,
            answer=""
        )
        self.test_question_answer3 = TestQuestionAnswer.objects.create(
            test_result=self.test_result,
            test_question=self.test_question3,
            answer=""
        )


    def test_GET_with_authorization_not_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_subscriber_iterate_all(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        for question in [self.test_question, self.test_question2, self.test_question3]:
            response = self.client.get(f'{self.URL}{question.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionSerializer(question, many=False).data
            self.assertEqual(response.data, serializer_data)

        for question in [self.test_question3, self.test_question2, self.test_question]:
            response = self.client.get(f'{self.URL}{question.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionSerializer(question, many=False).data
            self.assertEqual(response.data, serializer_data)

        for question in [self.test_question] * 3:
            response = self.client.get(f'{self.URL}{question.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionSerializer(question, many=False).data
            self.assertEqual(response.data, serializer_data)
        
        for question in [self.test_question2] * 3:
            response = self.client.get(f'{self.URL}{question.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionSerializer(question, many=False).data
            self.assertEqual(response.data, serializer_data)

        for question in [self.test_question3] * 3:
            response = self.client.get(f'{self.URL}{question.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionSerializer(question, many=False).data
            self.assertEqual(response.data, serializer_data)

    def test_GET_with_authorization_subscriber_iterate_all_with_answers(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # отвечаем на вопросы
        self.test_question_answer.answer="0"
        self.test_question_answer2.answer="1"
        self.test_question_answer3.answer="abc"
        self.test_question_answer.save()
        self.test_question_answer2.save()
        self.test_question_answer3.save()

        for question in [self.test_question, self.test_question2, self.test_question3]:
            response = self.client.get(f'{self.URL}{question.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionSerializer(question, many=False).data
            self.assertEqual(response.data, serializer_data)

        for question in [self.test_question2] * 3:
            response = self.client.get(f'{self.URL}{question.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionSerializer(question, many=False).data
            self.assertEqual(response.data, serializer_data)


### ONE ### ПРЯМОЙ ПОРЯДОК ВОПРОСОВ ### ЕСТЬ АКТИВНАЯ ПОПЫТКА ПРОХОЖДЕНИЯ
class TestQuestion_Retrieve_One_ACTIVE_Straight_ApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question/'

        self.client = APIClient()
        self.user_teacher = User.objects.create(username='teacher', email='user1@example.com')
        self.user_subscriber = User.objects.create(username='subscriber', email='user2@example.com')
        self.user_not_subscriber = User.objects.create(username='not subscriber', email='user3@example.com')

        self.token_teacher = Token.objects.create(user=self.user_teacher)
        self.token_subscriber = Token.objects.create(user=self.user_subscriber)
        self.token_not_subscriber = Token.objects.create(user=self.user_not_subscriber)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            shuffle=False,
            start=timezone.now() + timedelta(milliseconds=20),
            end=timezone.now() + timedelta(milliseconds=2000),
            duration=timedelta(milliseconds=1000)
        )

        self.test_question = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="one",
            answer_values="баг\nфича",
            answer_true="0"
        )
        self.test_question2 = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="one",
            answer_values="баг\nфича",
            answer_true="1"
        )
        self.test_question3 = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="free",
            answer_values="",
            answer_true="баг"
        )

        self.course.owners.add(self.user_teacher)
        self.course.students.add(self.user_subscriber)

        sleep(0.020)
        self.test_result = TestResult.objects.create(test=self.test, user=self.user_subscriber)

        self.test_question_answer = TestQuestionAnswer.objects.create(
            test_result=self.test_result,
            test_question=self.test_question,
            answer=""
        )
        self.test_question_answer2 = TestQuestionAnswer.objects.create(
            test_result=self.test_result,
            test_question=self.test_question2,
            answer=""
        )
        self.test_question_answer3 = TestQuestionAnswer.objects.create(
            test_result=self.test_result,
            test_question=self.test_question3,
            answer=""
        )

    def test_GET_with_authorization_not_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        response = self.client.get(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_subscriber_first(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        response = self.client.get(f'{self.URL}{self.test_question.id}/')
        serializer_data = TestQuestionSerializer(self.test_question, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)

    def test_GET_with_authorization_subscriber_second(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)
        response = self.client.get(f'{self.URL}{self.test_question2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_GET_with_authorization_subscriber_third(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)
        response = self.client.get(f'{self.URL}{self.test_question3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_GET_with_authorization_subscriber_many_times(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        for i in range(3):
            response = self.client.get(f'{self.URL}{self.test_question.id}/')
            serializer_data = TestQuestionSerializer(self.test_question, many=False).data

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, serializer_data)

    def test_GET_with_authorization_subscriber_answer_1(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # отвечаем на вопрос
        self.test_question_answer.answer="0"
        self.test_question_answer.save()

        response = self.client.get(f'{self.URL}{self.test_question.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f'{self.URL}{self.test_question3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_GET_with_authorization_subscriber_answer_2(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # отвечаем на вопрос
        self.test_question_answer.answer="0"
        self.test_question_answer.save()

        self.test_question_answer2.answer="1"
        self.test_question_answer2.save()

        response = self.client.get(f'{self.URL}{self.test_question.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question3.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_GET_with_authorization_subscriber_answer_3(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # отвечаем на вопрос
        self.test_question_answer.answer="0"
        self.test_question_answer.save()

        self.test_question_answer2.answer="1"
        self.test_question_answer2.save()

        self.test_question_answer3.answer="abc"
        self.test_question_answer3.save()

        response = self.client.get(f'{self.URL}{self.test_question.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestQuestionCreateApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')

        self.token_owner = Token.objects.create(user=self.user_owner)
        self.token_not_owner = Token.objects.create(user=self.user_not_owner)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            start=timezone.now() + timedelta(milliseconds=50),
            end=timezone.now() + timedelta(milliseconds=2000),
            duration=timedelta(milliseconds=1000)
        )

        self.course.owners.add(self.user_owner)

    def test_CREATE_without_authorization(self):
        ''''''
        self.client.credentials()

        data = {}
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_CREATE_with_authorization_not_owner(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        data = {}
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_CREATE_with_authorization_owner_test_started(self):
        '''тест начался'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        sleep(0.050)
        data = {}
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_CREATE_with_authorization_owner_test_not_started_empty(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)
        data = {}
        response = self.client.post(self.URL, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_CREATE_with_authorization_owner_test_not_started_empty2(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = { "test": self.test.pk }
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'answer_true': ['Обязательное поле.'],
            'answer_type': ['Обязательное поле.'],
            'answer_values': ['Обязательное поле.'],
            'max_mark': ['Обязательное поле.'],
            'question_text': ['Обязательное поле.']
        })

    def test_CREATE_with_authorization_owner_test_not_started_invalid_free(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'test': self.test.pk,
            'max_mark': Decimal(5),
            'question_text': 'какой вопрос?',
            'answer_type': 'free',
            'answer_values': '123',
            'answer_true': 'да',
        }
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer_values": ["incorrect"]
        })

    def test_CREATE_with_authorization_owner_test_not_started_invalid_one(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'test': self.test.pk,
            'max_mark': Decimal(5),
            'question_text': 'какой вопрос?',
            'answer_type': 'one',
            'answer_values': 'да\nнет',
            'answer_true': 'abc',
        }
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer_true": ["incorrect"]
        })

    def test_CREATE_with_authorization_owner_test_not_started_invalid_many(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'test': self.test.pk,
            'max_mark': Decimal(5),
            'question_text': 'какой вопрос?',
            'answer_type': 'many1',
            'answer_values': 'да',
            'answer_true': 'abc',
        }
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer_values": ["incorrect"],
            "answer_true": ["incorrect"]
        })

    def test_CREATE_with_authorization_owner_test_not_started_valid_free(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'test': self.test.pk,
            'question_text': 'какой вопрос?',
            'answer_type': 'free',
            'max_mark': Decimal(5),
            'answer_values': '',
            'answer_true': 'да',
        }
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'answer_true': 'да',
            'answer_type': 'free',
            'answer_values': '',
            'max_mark': 5.0,
            'question_text': 'какой вопрос?',
            'test': 1,
        })

    def test_CREATE_with_authorization_owner_test_not_started_valid_one(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'test': self.test.pk,
            'question_text': 'какой вопрос?',
            'answer_type': 'one',
            'max_mark': Decimal(5),
            'answer_values': 'да\nнет',
            'answer_true': '0',
        }
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'answer_true': '0',
            'answer_type': 'one',
            'answer_values': 'да\nнет',
            'max_mark': 5.0,
            'question_text': 'какой вопрос?',
            'test': 1,
        })

    def test_CREATE_with_authorization_owner_test_not_started_valid_many1(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'test': self.test.pk,
            'question_text': 'какой вопрос?',
            'answer_type': 'many1',
            'max_mark': Decimal(5),
            'answer_values': 'да\nнет\nне знаю',
            'answer_true': '0 2',
        }
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'answer_true': '0 2',
            'answer_type': 'many1',
            'answer_values': 'да\nнет\nне знаю',
            'max_mark': 5.0,
            'question_text': 'какой вопрос?',
            'test': 1,
        })

    def test_CREATE_with_authorization_owner_test_not_started_valid_many2(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        data = {
            'test': self.test.pk,
            'question_text': 'какой вопрос?',
            'answer_type': 'many2',
            'max_mark': Decimal(5),
            'answer_values': 'да\nнет\nне знаю',
            'answer_true': '0 2',
        }
        response = self.client.post(self.URL, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'answer_true': '0 2',
            'answer_type': 'many2',
            'answer_values': 'да\nнет\nне знаю',
            'max_mark': 5.0,
            'question_text': 'какой вопрос?',
            'test': 1,
        })


class TestQuestionDeleteApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question/'

        self.client = APIClient()
        self.user_owner = User.objects.create(username='owner', email='user2@example.com')
        self.user_not_owner = User.objects.create(username='not owner', email='user1@example.com')

        self.token_owner = Token.objects.create(user=self.user_owner)
        self.token_not_owner = Token.objects.create(user=self.user_not_owner)

        self.course = Course.objects.create(title='курс')
        self.course_element = CourseElement.objects.create(course=self.course, title='элемент курса')
        self.test = Test.objects.create(
            course_element=self.course_element,
            title='тест',
            mark_outer=Decimal(10),
            test_type='one',
            start=timezone.now() + timedelta(milliseconds=50),
            end=timezone.now() + timedelta(milliseconds=2000),
            duration=timedelta(milliseconds=1000)
        )
        self.test_question = TestQuestion.objects.create(
            test=self.test,
            question_text="баг или фича?",
            max_mark=Decimal(1),
            answer_type="one",
            answer_values="баг\nфича",
            answer_true="0"
        )

        self.course.owners.add(self.user_owner)


    def test_DELETE_invalid_pk(self):
        """"""
        response = self.client.delete(f'{self.URL}-1/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_DELETE_invalid_pk2(self):
        """"""
        response = self.client.delete(f'{self.URL}abc/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_DELETE_with_authorization_invalid_pk3(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.delete(f'{self.URL}100/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_DELETE_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.delete(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

    def test_DELETE_with_authorization_not_owner(self):
        '''Тест отображается только тем кто подписан на курс'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_owner.key)

        response = self.client.delete(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_DELETE_with_authorization_owner_test_not_started(self):
        '''тест не начался. его можно удалить'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        response = self.client.delete(f'{self.URL}{self.test_question.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

    def test_DELETE_with_authorization_owner_test_started(self):
        '''тест начался. его нельзя удалить'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_owner.key)

        sleep(0.050)
        response = self.client.delete(f'{self.URL}{self.test_question.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })