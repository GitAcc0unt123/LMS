from datetime import timedelta
from decimal import Decimal
from time import sleep

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from LMS.models import Course, CourseElement, Test, TestQuestion, TestResult, TestQuestionAnswer
from LMS_API.serializers import TestQuestionAnswerRetrieveSerializer


class TestQuestionAnswerApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question-answer/'
        self.client = APIClient()

        self.user_subscriber = User.objects.create(username='owner', email='user2@example.com')
        self.token_subscriber = Token.objects.create(user=self.user_subscriber)

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

        self.course.students.add(self.user_subscriber)
        sleep(0.010)

        self.test_result = TestResult.objects.create(test=self.test, user=self.user_subscriber)
        self.test_question_answer = TestQuestionAnswer.objects.create(
            test_result=self.test_result,
            test_question=self.test_question,
            answer="1"
        )


    def test_OPTIONS(self):
        '''допустимые методы'''

        response = self.client.options(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.has_header('Allow'))

    def test_NOT_ALOWED(self):
        '''методы не разрешены'''

        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.patch(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.head(self.URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_OPTIONS_PK(self):
        '''допустимые методы'''

        response = self.client.options(f'{self.URL}{self.test_question_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Allow'))
        self.assertEqual(response['allow'], 'GET, PATCH, HEAD, OPTIONS')

    def test_NOT_ALOWED_PK(self):
        '''методы не разрешены'''

        response = self.client.post(f'{self.URL}{self.test_question_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"POST\" не разрешен.'})

        response = self.client.put(f'{self.URL}{self.test_question_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"PUT\" не разрешен.'})

        response = self.client.delete(f'{self.URL}{self.test_question_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {'detail': 'Метод \"DELETE\" не разрешен.'})


### MANY ### считаем что в many прямой и случайные порядки вопросов работают одинаково
class TestQuestionAnswer_Retrieve_Many_ApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question-answer/'

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
            title='тест MANY',
            mark_outer=Decimal(10),
            test_type='many',
            shuffle=False,
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

        sleep(0.010)
        # создаём прохождение теста
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

        response = self.client.get(f'{self.URL}999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

##### без действующей попытки прохождения теста
    def test_GET_with_authorization_not_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)
        response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_subscriber_without_attempt(self):
        ''''''
        # завершаем активное прохождение теста
        self.test_result.end = timezone.now()
        self.test_result.save(update_fields=['end'])

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)
        response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_teacher(self):
        '''преподавателю может смотреть все ответы'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')
        serializer_data = TestQuestionAnswerRetrieveSerializer(self.test_question_answer, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)

##### действующая попытка прохождения попытки
    def test_GET_with_authorization_subscriber_iterate_all(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        for answer in [self.test_question_answer, self.test_question_answer2, self.test_question_answer3]:
            response = self.client.get(f'{self.URL}{answer.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionAnswerRetrieveSerializer(answer, many=False).data
            self.assertEqual(response.data, serializer_data)

    def test_GET_with_authorization_subscriber_iterate_all_reverse(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        for answer in [self.test_question_answer3, self.test_question_answer2, self.test_question_answer]:
            response = self.client.get(f'{self.URL}{answer.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionAnswerRetrieveSerializer(answer, many=False).data
            self.assertEqual(response.data, serializer_data)

    def test_GET_with_authorization_subscriber_iterate_loop(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        for i in range(3):
            response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionAnswerRetrieveSerializer(self.test_question_answer, many=False).data
            self.assertEqual(response.data, serializer_data)
        
        for i in range(3):
            response = self.client.get(f'{self.URL}{self.test_question_answer2.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionAnswerRetrieveSerializer(self.test_question_answer2, many=False).data
            self.assertEqual(response.data, serializer_data)

        for i in range(3):
            response = self.client.get(f'{self.URL}{self.test_question_answer3.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionAnswerRetrieveSerializer(self.test_question_answer3, many=False).data
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

        for answer in [self.test_question_answer, self.test_question_answer2, self.test_question_answer3]:
            response = self.client.get(f'{self.URL}{answer.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionAnswerRetrieveSerializer(answer, many=False).data
            self.assertEqual(response.data, serializer_data)

        for answer in [self.test_question_answer2] * 3:
            response = self.client.get(f'{self.URL}{answer.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            serializer_data = TestQuestionAnswerRetrieveSerializer(answer, many=False).data
            self.assertEqual(response.data, serializer_data)


### ONE ### ЕСТЬ АКТИВНАЯ ПОПЫТКА ПРОХОЖДЕНИЯ
### ПРЯМОЙ И СЛУЧАЙНЫЙ ПОРЯДОК ВОПРОСОВ НЕ ОТЛИЧАЮТСЯ ПРОХОЖДЕНИЕМ
### отличие только в порядке создания TestQuestionAnswer из вопросов теста
class TestQuestionAnswer_Retrieve_One_ACTIVE_Straight_ApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question-answer/'

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

        response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_GET_with_authorization_subscriber_first(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')
        serializer_data = TestQuestionAnswerRetrieveSerializer(self.test_question_answer, many=False).data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data)

    def test_GET_with_authorization_subscriber_second(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)
        response = self.client.get(f'{self.URL}{self.test_question_answer2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_GET_with_authorization_subscriber_third(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)
        response = self.client.get(f'{self.URL}{self.test_question_answer3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_GET_with_authorization_subscriber_many_times(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        for i in range(3):
            response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')
            serializer_data = TestQuestionAnswerRetrieveSerializer(self.test_question_answer, many=False).data

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, serializer_data)

    def test_GET_with_authorization_subscriber_answer_1(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # отвечаем на вопрос
        self.test_question_answer.answer="0"
        self.test_question_answer.save()

        response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question_answer2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f'{self.URL}{self.test_question_answer3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_GET_with_authorization_subscriber_answer_2(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # отвечаем на вопрос
        self.test_question_answer.answer="0"
        self.test_question_answer.save()

        self.test_question_answer2.answer="1"
        self.test_question_answer2.save()

        response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question_answer2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question_answer3.id}/')
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

        response = self.client.get(f'{self.URL}{self.test_question_answer.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question_answer2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'{self.URL}{self.test_question_answer3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


########################## UPDATE ##########################

### MANY ### считаем что в many прямой и случайные порядки вопросов работают одинаково
class TestQuestionAnswer_Update_Many_ApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question-answer/'

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
            title='тест MANY',
            mark_outer=Decimal(10),
            test_type='many',
            shuffle=False,
            number_of_attempts=1,
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

        sleep(0.010)
        # создаём прохождение теста
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


    def test_PATCH_invalid_pk(self):
        """"""
        data = {}
        response = self.client.patch(f'{self.URL}-1/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PATCH_invalid_pk2(self):
        """"""
        data = {}
        response = self.client.patch(f'{self.URL}abc/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PATCH_invalid_pk3(self):
        """"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        response = self.client.patch(f'{self.URL}999/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PATCH_without_authorization(self):
        '''Доступ неавторизованного пользователя'''
        self.client.credentials()

        data = {}
        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "Учетные данные не были предоставлены."
        })

##### без действующей попытки прохождения теста
    def test_PATCH_with_authorization_not_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        data = {}
        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PATCH_with_authorization_subscriber_without_attempt(self):
        ''''''
        # завершаем активное прохождение теста
        self.test_result.end = timezone.now()
        self.test_result.save(update_fields=['end'])

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {}
        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PATCH_with_authorization_teacher(self):
        '''преподавателю не может изменять ответы на вопросы'''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_teacher.key)

        data = {}
        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

##### действующая попытка прохождения попытки
    def test_PATCH_with_authorization_subscriber_iterate_all(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # прямой порядок
        data = {'answer': '0'}
        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')
        #self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer": "0"
        })

        data = {'answer': '1'}
        response = self.client.patch(f'{self.URL}{self.test_question_answer2.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer": "1"
        })

        data = {'answer': 'abc'}
        response = self.client.patch(f'{self.URL}{self.test_question_answer3.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer": "abc"
        })

    def test_PATCH_with_authorization_subscriber_iterate_all_reverse(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # обратный порядок
        data = {'answer': 'abc'}
        response = self.client.patch(f'{self.URL}{self.test_question_answer3.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer": "abc"
        })

        data = {'answer': '1'}
        response = self.client.patch(f'{self.URL}{self.test_question_answer2.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer": "1"
        })

        data = {'answer': '0'}
        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer": "0"
        })

    def test_PATCH_with_authorization_subscriber_iterate_loop(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        for i in range(3):
            data = {'answer': "0"}
            response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertJSONEqual(response.content.decode('utf-8'), {
                "answer": "0"
            })
        
        for i in range(3):
            data = {'answer': "1"}
            response = self.client.patch(f'{self.URL}{self.test_question_answer2.id}/', data=data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertJSONEqual(response.content.decode('utf-8'), {
                "answer": "1"
            })

        for i in range(3):
            data = {'answer': "abc"}
            response = self.client.patch(f'{self.URL}{self.test_question_answer3.id}/', data=data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertJSONEqual(response.content.decode('utf-8'), {
                "answer": "abc"
            })

##### проверить как неправильный формат вопросов работает
##### потестить вычисление оценки

### ONE ### ЕСТЬ АКТИВНАЯ ПОПЫТКА ПРОХОЖДЕНИЯ
### ПРЯМОЙ И СЛУЧАЙНЫЙ ПОРЯДОК ВОПРОСОВ НЕ ОТЛИЧАЮТСЯ ПРОХОЖДЕНИЕМ
### отличие только в порядке создания TestQuestionAnswer из вопросов теста
class TestQuestionAnswer_Update_One_ACTIVE_Straight_ApiTestCase(APITestCase):
    ''''''
    def setUp(self):
        """Method called to prepare the test fixture. This is called immediately before calling the test method"""
        self.URL = '/api-lms/test-question-answer/'

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

    def test_PATCH_with_authorization_not_subscriber(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_not_subscriber.key)

        data = {}
        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "detail": "У вас недостаточно прав для выполнения данного действия."
        })

    def test_PATCH_with_authorization_subscriber_first(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        data = {'answer': '0'}
        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "answer": "0"
        })

    def test_PATCH_with_authorization_subscriber_second(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)
        data = {'answer': '1'}
        response = self.client.patch(f'{self.URL}{self.test_question_answer2.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_PATCH_with_authorization_subscriber_third(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)
        data = {'answer': 'abc'}
        response = self.client.patch(f'{self.URL}{self.test_question_answer3.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_PATCH_with_authorization_subscriber_answer_1(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # отвечаем на вопрос
        self.test_question_answer.answer="0"
        self.test_question_answer.save()

        data = {'answer': '1'}

        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(f'{self.URL}{self.test_question_answer3.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(f'{self.URL}{self.test_question_answer2.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_PATCH_with_authorization_subscriber_answer_2(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # отвечаем на вопрос
        self.test_question_answer.answer="0"
        self.test_question_answer.save()

        self.test_question_answer2.answer="1"
        self.test_question_answer2.save()

        data = {'answer': 'abc'}

        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(f'{self.URL}{self.test_question_answer2.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(f'{self.URL}{self.test_question_answer3.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_PATCH_with_authorization_subscriber_answer_3(self):
        ''''''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_subscriber.key)

        # отвечаем на вопрос
        self.test_question_answer.answer="0"
        self.test_question_answer.save()

        self.test_question_answer2.answer="1"
        self.test_question_answer2.save()

        self.test_question_answer3.answer="abc"
        self.test_question_answer3.save()

        data = {'answer': '1'}

        response = self.client.patch(f'{self.URL}{self.test_question_answer.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(f'{self.URL}{self.test_question_answer2.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(f'{self.URL}{self.test_question_answer3.id}/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)