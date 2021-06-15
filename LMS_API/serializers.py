from django.contrib.auth.models import User

from rest_framework import serializers

from LMS.models import (
    Course,
    CourseElement,
    Task,
    TaskAnswer,
    TaskAnswerMark,
    TaskTest,
    Test,
    TestResult,
    TestQuestion,
    Notification,
    Comment,
    FileStorage,
    TestQuestionAnswer,
    UserData,
)

# https://www.django-rest-framework.org/api-guide/serializers/

# сериализаторы производят только проверки полей модели и unique, UniqueTogether
# для проверки на уровне моделей нужно написать проверки в методе validate
# или через форма+is_valid или model+clean
# https://www.django-rest-framework.org/api-guide/serializers/#validation

class UserDetailSerializer(serializers.ModelSerializer): # HyperlinkedModelSerializer
    ''''''
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email']

class UserDataSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = UserData
        fields = ['user', 'dark_mode', 'send_notifications_to_email', 'delete_time']
        read_only_fields = ['user']

###
class FileStorageShortSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = FileStorage
        fields = ['id', 'filename']
class TaskShortSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = Task
        fields = ['id', 'title']
class TestShortSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = Test
        fields = ['id', 'title']
class CommentShortSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = Comment
        fields = ['user', 'text', 'datetime']

# COURSE ELEMENT
class CourseElementSerializer(serializers.ModelSerializer):
    '''создавать элемент курса'''
    files = FileStorageShortSerializer(many=True)
    tasks = TaskShortSerializer(many=True)
    tests = TestShortSerializer(many=True)

    class Meta:
        model = CourseElement
        fields = ['id', 'course', 'title', 'description', 'files', 'tasks', 'tests']
        read_only_fields = ['course', 'files', 'tasks', 'tests']

class CourseElementCreateSerializer(serializers.ModelSerializer):
    '''редактировать элемент курса'''
    class Meta:
        model = CourseElement
        fields = ['id', 'course', 'title', 'description']

class CourseElementUpdateSerializer(serializers.ModelSerializer):
    '''редактировать элемент курса'''
    class Meta:
        model = CourseElement
        fields = ['id', 'title', 'description']
        read_only_fields = ['course']

# COURSE
class CourseRetrieveSerializer(serializers.ModelSerializer):
    '''подробно один курс'''
    course_elements = CourseElementSerializer(many=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'course_elements']
        read_only_fields = ['course_elements']

class CourseUpdateSerializer(serializers.ModelSerializer):
    '''редактирование курса'''
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'key']

class CourseListSerializer(serializers.ModelSerializer):
    '''кратко список курсов'''
    class Meta:
        model = Course
        fields = ['id', 'title']

class CourseStudentsSerializer(serializers.ModelSerializer):
    '''список студентов записанных на курс'''
    # https://www.django-rest-framework.org/api-guide/relations/#slugrelatedfield
    students = serializers.SlugRelatedField(slug_field='username', read_only=True, many=True)

    class Meta:
        model = Course
        fields = ['id', 'students']

# TASK
class TaskSerializer(serializers.ModelSerializer):
    '''создать задание'''
    # если комментарии включены и неудалённые
    comments = serializers.SerializerMethodField('get_comments')

    def get_comments(self, task):
        queryset = Comment.objects.filter(deleted=False, task=task)
        serializer = CommentShortSerializer(instance=queryset, many=True)
        return serializer.data

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['comments']

class TaskUpdateSerializer(serializers.ModelSerializer):
    '''редактировать задание'''
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['course_element', 'execute_answer']

class TaskTestSerializer(serializers.ModelSerializer):
    '''для тестов к заданиям с автоматической проверкой'''
    class Meta:
        model = TaskTest
        fields = ['id', 'task', 'input', 'output', 'hidden']

class TaskAnswerSerializer(serializers.ModelSerializer):
    ''''''
    files = FileStorageShortSerializer(many=True, read_only=True)
    #прикрутить файлы и read-only оценку если стоит
    #приделать чтобы показывал execute_answer
    class Meta:
        model = TaskAnswer
        fields = ['id', 'task', 'student', 'datetime_load', 'files', 'language', 'code']
        read_only_fields = ['id', 'task', 'student', 'datetime_load', 'files', 'language', 'code']

class TaskAnswerMarkSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = TaskAnswerMark
        fields = '__all__'

# TEST
class TestSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = Test
        exclude = ['course_element']

class TestCreateSerializer(serializers.ModelSerializer):
    '''для создание теста'''
    class Meta:
        model = Test
        #exclude = ['start', 'end']
        fields = '__all__'

class TestQuestionSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = TestQuestion
        fields = ['question_text', 'max_mark', 'answer_type', 'answer_values']

class TestQuestionAnswerUpdateSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = TestQuestionAnswer
        fields = ['answer']

class TestQuestionAnswerRetrieveSerializer(serializers.ModelSerializer):
    ''''''
    test_question = serializers.SlugRelatedField(slug_field='question_text', read_only=True)
    answer_type = serializers.SerializerMethodField('answer_type_func')

    def answer_type_func(self, test_result):
        return test_result.test_question.answer_type

    class Meta:
        model = TestQuestionAnswer
        fields = ['test_result', 'test_question', 'answer_type', 'answer']

class TestResultListSerializer(serializers.ModelSerializer):
    ''''''
    finished = serializers.SerializerMethodField('is_finished')
    mark = serializers.SerializerMethodField('evaluate_mark')
    end = serializers.SerializerMethodField('evaluate_end')
    test_type = serializers.SerializerMethodField('test_type_func')
    current_question = serializers.SerializerMethodField('current_question_func')

    def current_question_func(self, test_result):
        # id текущего TestQuestionAnswer. первый объект без ответа в порядке возрастания id
        obj = test_result.test_result_questions_answers.filter(answer="").order_by('id').first()
        return obj.id if obj else None

    def test_type_func(self, test_result):
        return test_result.test.test_type

    def is_finished(self, test_result):
        return test_result.is_finished()
    
    def evaluate_mark(self, test_result):
        return test_result.evaluate_mark()

    def evaluate_end(self, test_result):
        if test_result.is_finished():
            return test_result.end if test_result.end else (test_result.start + test_result.test.duration)
        else:
            return None

    class Meta:
        model = TestResult
        fields = ['id', 'mark', 'start', 'end', 'finished', 'test_type', 'current_question', 'test_result_questions_answers']


class TestResultRetrieveSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = TestResult
        fields = '__all__'

# OTHER
class NotificationSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = Notification
        fields = ['id', 'text', 'datetime', 'readed']
        read_only_fields = ['text', 'datetime', 'readed']

class CommentSerializer(serializers.ModelSerializer):
    ''''''
    class Meta:
        model = Comment
        fields = ['id', 'task', 'text', 'datetime', 'visible']
        read_only_fields = ['id', 'datetime', 'visible']