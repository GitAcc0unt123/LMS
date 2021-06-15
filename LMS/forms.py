from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.auth.models import User

from .models import PROGRAMMING_LANGUAGE, TestResult
from .models import (
    Course,
    CourseElement,
    Task,
    TaskAnswer,
    TaskAnswerMark,
    TaskTest,
    Test,
    TestQuestion,
    TestQuestionAnswer,
    Comment,
    FileStorage,
)


class MyUserChangeForm(forms.ModelForm):
    '''форма для изменения данных пользователя'''
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class CourseEditModelForm(forms.ModelForm):
    '''форма для редактирование курса'''
    class Meta:
        model = Course
        fields = ['title', 'description', 'groups', 'key']
        labels = {
            # по умолчанию описание берётся из модели
        }
        widgets = {
            'title':forms.TextInput(attrs={ 'size':100 }),
            'description':forms.Textarea(attrs={ 'cols':100, 'rows':5 }),
        }
        field_classes = {

        }

class CourseElementModelForm(forms.ModelForm):
    '''форма для создания элемента курса'''
    class Meta:
        model = CourseElement
        fields = ['title', 'description']
        widgets = {
            'title':forms.TextInput(attrs={ 'size':100 }),
            'description':forms.Textarea(attrs={ 'cols':100, 'rows':5 }),
        }


class TaskExecOffModelForm(forms.ModelForm):
    '''форма для создания и редактирования задания с ручной проверкой'''
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'comments_is_on',
            'deadline_visible',
            'deadline_true',
            'mark_outer',
            'mark_max',
            'limit_files_count',
            'limit_files_memory_MB',
            ]

        widgets = {
            'title':forms.TextInput(attrs={ 'size':100 }),
            'description':forms.Textarea(attrs={ 'cols':100, 'rows':10 }),

            'deadline_visible': AdminSplitDateTime(),
            'deadline_true': AdminSplitDateTime(),

            'mark_outer': forms.NumberInput(attrs={ 'min':0, 'max':1000 }),
            'mark_max': forms.NumberInput(attrs={ 'min':0, 'max':1000 }),

            'limit_files_count': forms.NumberInput(attrs={ 'max':32 }),
            'limit_files_memory': forms.NumberInput(attrs={ 'max':128 }),
        }
        field_classes = {
            # Allow specifying form field types in a ModelForm's Meta
            'deadline_visible': forms.SplitDateTimeField,
            'deadline_true': forms.SplitDateTimeField,
        }

class TaskExecOnModelForm(forms.ModelForm):
    '''форма для создания и редактирования задания с автоматической проверкой'''
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'comments_is_on',
            'deadline_visible',
            'deadline_true',
            'mark_outer',
            'mark_max',
            'start_code',
            'limit_time',
            'limit_memory_Mbyte',
            ]
        widgets = {
            'title':forms.TextInput(attrs={ 'size':100 }),
            'description':forms.Textarea(attrs={ 'cols':100, 'rows':10 }),

            'deadline_visible': AdminSplitDateTime(),
            'deadline_true': AdminSplitDateTime(),

            'mark_outer': forms.NumberInput(attrs={ 'min':0, 'max':1000 }),
            'mark_max': forms.NumberInput(attrs={ 'min':0, 'max':1000 }),

            'limit_memory_Mbyte': forms.NumberInput(attrs={ 'max':1024 }),
        }
        field_classes = {
            # Allow specifying form field types in a ModelForm's Meta
            'deadline_visible': forms.SplitDateTimeField,
            'deadline_true': forms.SplitDateTimeField,
        }

class TaskModelForm(forms.ModelForm):
    '''форма для создания и редактирования задачи'''
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'comments_is_on',
            'deadline_visible',
            'deadline_true',
            'mark_outer',
            'mark_max',
            'execute_answer',
            'start_code',
            'limit_time',
            'limit_memory_Mbyte',
            #'STACK_Kbyte',
            ]

        widgets = {
            'title':forms.TextInput(attrs={ 'size':100 }),
            'description':forms.Textarea(attrs={ 'cols':100, 'rows':10 }),

            'deadline_visible': AdminSplitDateTime(),
            'deadline_true': AdminSplitDateTime(),

            'mark_outer': forms.NumberInput(attrs={ 'min':0, 'max':1000 }),
            'mark_max': forms.NumberInput(attrs={ 'min':0, 'max':1000 }),

            'limit_files_count': forms.NumberInput(attrs={ 'max':32 }),
            'limit_files_memory': forms.NumberInput(attrs={ 'max':128 }),

            'limit_memory_Mbyte': forms.NumberInput(attrs={ 'max':1024 }),
        }
        field_classes = {
            # Allow specifying form field types in a ModelForm's Meta
            'deadline_visible': forms.SplitDateTimeField,
            'deadline_true': forms.SplitDateTimeField,
        }
        validators = {
            # inherited from model validators
        }

class TaskAnswerCodeModelForm(forms.ModelForm):
    ''''''
    class Meta:
        model = TaskAnswer
        fields = ['task', 'student', 'language', 'code', 'is_running']

class TaskAnswerMarkModelForm(forms.ModelForm):
    '''поля для оценивания ответа на задачу'''
    class Meta:
        model = TaskAnswerMark
        fields = '__all__'

class TaskTestModelForm(forms.ModelForm):
    ''''''
    class Meta:
        model = TaskTest
        fields = ['task', 'input', 'output', 'hidden']

    def __init__(self, *args, **kwargs):
        super(TaskTestModelForm, self).__init__(*args, **kwargs)

        self.fields['input'].required = False
        self.fields['hidden'].required = True

class CodeForm(forms.Form):
    '''форма для загрузки кода'''
    language = forms.ChoiceField(choices=PROGRAMMING_LANGUAGE, required=True, label='язык программирования')

    def __init__(self,*args,**kwargs):
        initial_code = kwargs.pop('initial_code')
        super(CodeForm, self).__init__(*args,**kwargs)

        self.fields['code'] = forms.CharField(widget=forms.Textarea(attrs={'placeholder':'добавить код'}), label='put your code here', max_length=1000, initial=initial_code)

class TestCreateModelForm(forms.ModelForm):
    """"""
    class Meta:
        model = Test
        fields = '__all__'

class TestChangeModelForm(forms.ModelForm):
    """"""
    class Meta:
        model = Test
        exclude = ['course_element']

    def __init__(self, *args, **kwargs):
        super(TestChangeModelForm, self).__init__(*args, **kwargs)

        self.fields['title'].required = False
        self.fields['mark_outer'].required = False
        self.fields['test_type'].required = False
        self.fields['start'].required = False
        self.fields['end'].required = False
        self.fields['duration'].required = False

class TestModelForm(forms.ModelForm):
    '''форма для создания и редактирования теста'''
    class Meta:
        model = Test
        exclude = ['course_element']
        labels = {
            # по умолчанию описание из модели берётся
        }
        widgets = {
            'title':forms.TextInput(attrs={ 'size':100 }),
            'description':forms.Textarea(attrs={ 'cols':100, 'rows':10 }),

            'mark_outer': forms.NumberInput(attrs={ 'min':0, 'max':1000 }),
            'number_of_attempts': forms.NumberInput(attrs={ 'min':1, 'max':32767, 'value':1, 'style':'width: 5em' }),
            'start': AdminSplitDateTime(),
            'end': AdminSplitDateTime(),
            'duration': forms.TimeInput(attrs={ 'value':'00:00:00' }),
        }
        # Allow specifying form field types in a ModelForm's Meta
        field_classes = {
            'start': forms.SplitDateTimeField,
            'end': forms.SplitDateTimeField,
        }

class TestResultChangeModelForm(forms.ModelForm):
    """"""
    class Meta:
        model = TestResult
        fields = '__all__'

class TestQuestionCreateModelForm(forms.ModelForm):
    """"""
    class Meta:
        model = TestQuestion
        fields = '__all__'

class TestQuestionModelForm(forms.ModelForm):
    '''используется для проверки данных из POST запроса'''
    class Meta:
        model = TestQuestion
        fields = [ 'question_text', 'max_mark', 'answer_type' ]

class TestQuestionAnswerModelForm(forms.ModelForm):
    ''''''
    class Meta:
        model = TestQuestionAnswer
        fields = ['answer']