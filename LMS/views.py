import os
import mimetypes
import logging

from django.http import HttpResponse, FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST

from django.utils import timezone # instead of python datetime

from django.conf import settings

from .forms import (
    MyUserChangeForm,
    CourseEditModelForm,
    CourseElementModelForm,
    TaskModelForm,
    TaskTestModelForm,
    CodeForm,
    TestModelForm,
    TestQuestionModelForm,
)
from .models import *

logger = logging.getLogger(__name__)


# в контексте шаблонов будут доступны значения
def context_processor_notices(request):
    if request.user.is_authenticated:
        return { 'notice_count': Notification.objects.filter(user=request.user, deleted=False).count() }
    else:
        return { 'authenticationForm': AuthenticationForm() }


def loginView(request):
    '''страница для авторизации пользователя'''
    if request.user.is_authenticated:
        return redirect('home')

    form = AuthenticationForm(data=request.POST or None)
    if form.is_valid():
        login(request, form.get_user()) # attach authenticated user to the current session
        return redirect(request.POST['next'] if 'next' in request.POST else 'home')

    next = request.GET['next'] if request.GET and 'next' in request.GET else None
    context = {
        'authenticationForm':form,
        'next':next,
    }
    return render(request, 'LMS/user/login.html', context)

@require_GET
def logoutView(request):
    '''разлогиниться'''
    if request.user.is_authenticated:
        logout(request)
    return redirect('home')

def registration(request):
    '''страница для регистрации пользователя'''
    if request.user.is_authenticated:
        return redirect('home')

    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        new_user = form.save()
        UserData.objects.create(user=new_user)
        login(request, new_user)
        return redirect('home')

    context = {
        'userCreationForm':form,
    }
    return render(request, 'LMS/user/registration.html', context)

# todo: send mail
def reset_password(request):
    '''восстановление пароля'''
    if request.user.is_authenticated:
        return redirect('home')

    form = PasswordResetForm(request.POST or None)
    if form.is_valid():
        return redirect('home')

    context = {
        'passwordResetForm': form,
    }
    return render(request, 'LMS/user/reset_password.html', context)

@require_GET
def privacy(request):
    '''политика конфиденциальности'''
    return render(request, 'LMS/privacy.html', {})

@require_GET
def about(request):
    '''о сайте'''
    return render(request, 'LMS/about.html', {})

@require_GET
def faq(request):
    '''FAQ'''
    return render(request, 'LMS/faq.html', {})

# todo: при ошибке выводить сообщение в /settings
@require_POST
@login_required
def update_password(request):
    '''изменить пароль'''
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)
        return redirect('/settings')

    return HttpResponse(form.errors)
    
# todo: при ошибке выводить сообщение в /settings
@require_POST
@login_required
def update_settings(request):
    '''изменить данные пользователя'''
    form = MyUserChangeForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('/settings')

    return HttpResponse(form.errors)
    
# todo: см. update_password & update_settings
@login_required(login_url='login')
def user_settings(request):
    '''формы для изменения данных пользователя и смены пароля'''
    userChangeForm = MyUserChangeForm(instance=request.user)
    passwordChangeForm = PasswordChangeForm(user=request.user)

    context = {
        'userChangeForm':userChangeForm,
        'passwordChangeForm':passwordChangeForm,
    }
    return render(request, 'LMS/user/settings.html', context)

# todo: refactoring. mb change database
@require_GET
@login_required(login_url='login')
def user_marks(request):
    '''показывает курсы на кот. подписан и оценки за эти курсы'''
    #tasks = [ (Task, mark, mark_max),  ]
    #tests = [ (Test, mark, mark_max),  ]

    #elem = ( tasks, mark, mark_max, tests, mark, mark_max )
    #course = [ (elem, elem_res, mark, mark_max), ]
    #courses = [ (course, course_res, mark, mark_max), ]

    courses_res = []
    courses = Course.objects.filter(students=request.user)

    for course in courses:
        course_res = []

        for elem in course.course_elements.all():
            tasks = elem.tasks.all()
            tasks = [ (task, task.get_mark(request.user), task.mark_outer) for task in tasks ]

            tests = elem.tests.all()
            tests = [ (test, test.get_user_mark(request.user), test.mark_outer) for test in tests ]

            tasks_mark = sum( 0 if mark is None else mark for _,mark,_ in tasks)
            tasks_mark_max = sum(mark_max for _,_,mark_max in tasks)

            tests_mark = sum(0 if mark is None else mark for _,mark,_ in tests)
            tests_mark_max = sum(mark_max for _,_,mark_max in tests)

            elem_res = [ ( tasks, tasks_mark, tasks_mark_max, tests, tests_mark, tests_mark_max ) ]

            elem_mark = elem_res[0][1] + elem_res[0][4]
            elem_mark_max = elem_res[0][2] + elem_res[0][5]
            course_res.append( (elem, elem_res, elem_mark, elem_mark_max) )

        course_mark = sum(mark for _,_,mark,_ in course_res)
        course_mark_max = sum(mark_max for _,_,_,mark_max in course_res)
        courses_res.append( (course, course_res, course_mark, course_mark_max) )

    context = {
        'courses':courses_res,
    }
    return render(request, 'LMS/user/marks.html', context)

@require_GET
@login_required(login_url='login')
def user_courses(request):
    '''выводит курсы на которые записан или ведёт пользователь'''
    courses_owner = Course.objects.filter(owners=request.user).order_by('title')
    courses_subscribe = Course.objects.filter(students=request.user).order_by('title')

    context = {
        'courses_owner': courses_owner,
        'courses_subscribe': courses_subscribe,
    }
    return render(request, 'LMS/course/user_courses.html', context)

# todo: refactoring
@require_GET
def courses(request):
    '''отображение всех курсов'''
    courses_all = Course.objects.all()

    query = request.GET['q'] if request.GET and 'q' in request.GET else None
    if query and query != '':
        # для SQLite чувствительна к __icontains=query
        courses_all = courses_all.filter(title__iregex=query) #костыльно, но работает на SQLite

    context = {
        'courses':courses_all.only('title'),
    }
    return render(request, 'LMS/course/all.html', context)


@require_GET
def course_view(request, id):
    '''отображение курса'''
    course = get_object_or_404(Course, pk=id)

    permission_subscribe = bool(
        request.user.is_authenticated and
        not course.students.filter(pk=request.user.pk).exists() and
        not course.excluded.filter(pk=request.user.pk).exists()
    )

    context = {
        'course':course,
        'course_description':course.description.split('\n'),
        'permission_edit':course.can_edit(request.user),
        'permission_subscribe':permission_subscribe,
        'in_group':course.groups.filter(pk__in=request.user.groups.all()).exists(),
        'is_subscriber':course.is_subscriber(request.user),
    }
    return render(request, 'LMS/course/detail.html', context)

@login_required(login_url='login')
def course_edit(request, id):
    '''редактирование курса ?'''
    course = get_object_or_404(Course, pk=id)

    # проверить права редактирования
    if not course.can_edit(request.user):
        return HttpResponseForbidden('нет прав для редактирования курса')

    if request.method == 'POST':
        courseEditForm = CourseEditModelForm(request.POST, instance=course)

        if courseEditForm.is_valid():
            courseEditForm.save()
            return redirect(f'/course/{id}/edit')
        else:
            print('invalid form')

    courseEditForm = CourseEditModelForm(instance=course)
    context = {
        'course':course,
        'users':course.students.all().order_by('username'),
        'courseEditForm':courseEditForm,
        'courseElementModelForm':CourseElementModelForm(),
    }
    return render(request, 'LMS/course/edit.html', context)

@require_POST
@login_required
def course_element_create(request, id):
    """добавить элемент курса ?"""
    course = get_object_or_404(Course, pk=id)

    # проверить права
    if not course.can_edit(request.user):
        return HttpResponseForbidden('нет прав для редактирования курса')

    form = CourseElementModelForm(request.POST)

    if form.is_valid():
        courseElement = form.save(commit=False)
        courseElement.course = course
        courseElement.save()

    return redirect(f'/course/{id}/edit')


@require_GET
@login_required(login_url='login')
def task_view(request, id):
    """отображает задание и форму для отправки ответа"""
    task = get_object_or_404(Task, pk=id)

    # проверить что записан на курс
    user_subscribe = task.course_element.course.is_subscriber(request.user)
    if not user_subscribe:
        return HttpResponseForbidden('вы не записаны на этот курс')

    task_answer = task.get_answer(request.user) if request.user.is_authenticated else None
    context = {
        'task':task,
        'comments':task.comments.filter(deleted=False) if task.comments_is_on else None,
        'task_description':task.description.split('\n'),
        'task_answer':task_answer,
        'user_subscribed':task.course_element.course.is_subscriber(request.user),
        'user_edit_task':task.course_element.course.can_edit(request.user),
        'can_set_task_answer':task.can_set_task_answer(request.user),
        'check_answers': len([x for x in TaskAnswer.objects.filter(task=task) if x.get_TaskAnswerMark() == None]) if task.course_element.course.can_edit(request.user) else 0,
        'CodeForm': CodeForm(initial_code=task.start_code) if task.execute_answer and task.can_set_task_answer(request.user) else None,
    }

    return render(request, 'LMS/task/view_automatic.html' if task.execute_answer else 'LMS/task/view_non_automatic.html', context)

@require_GET
@login_required(login_url='login')
def task_evaluate(request, id):
    """страница для оценивания работ"""
    task = get_object_or_404(Task, pk=id)

    # проверка прав
    if not task.course_element.course.owners.filter(id=request.user.id).exists():
        return HttpResponseForbidden('нет прав для оценивания задач')

    context = {
        'task': task,
        'task_answers': [ task_answer for task_answer in task.task_answers.all().order_by('task_answer_mark') ]
    }
    return render(request, 'LMS/task/evaluate.html', context)

@login_required(login_url='login')
def task_edit(request, id):
    """редактирование задания"""
    task = get_object_or_404(Task, pk=id)

    if not task.can_edit_task(request.user):
        return HttpResponseForbidden('нет прав для редактирования задачи')

    taskModelForm = TaskModelForm(request.POST or None, instance=task)

    if taskModelForm.is_valid():
        taskModelForm.save()
        return redirect(f'/task/{id}')

    context = {
        'taskModelForm':taskModelForm,
    }
    return render(request, 'LMS/task/edit.html', context)

@login_required
def task_create(request, course_element_id):
    """создать задание"""
    course_element = get_object_or_404(CourseElement, pk=course_element_id)

    if not course_element.course.can_edit(request.user):
        return HttpResponseForbidden('нет прав для создания задачи')

    taskModelForm = TaskModelForm(request.POST or None)
    if taskModelForm.is_valid():
        task = taskModelForm.save(commit=False)
        task.course_element = course_element

        # найти способ получше
        try:
            task.validate_unique()
            task.save()
            return redirect(f'/task/{task.id}')
        except ValidationError as e:
            taskModelForm.add_error(None, e)

    context = {
        'taskModelForm':taskModelForm,
    }
    return render(request, 'LMS/task/create.html', context)

@require_GET
@login_required(login_url='login')
def task_tests(request, id):
    """страница для создания и удаления тестов задач с автоматической проверкой ответов"""
    task = get_object_or_404(Task, pk=id, execute_answer=True)

    # проверка прав
    if not task.course_element.course.owners.filter(id=request.user.id).exists():
        return HttpResponseForbidden('нет прав')

    context = {
        'task': task,
        'taskTestModelForm': TaskTestModelForm(),
    }
    return render(request, 'LMS/task/tests.html', context)


@require_GET
@login_required(login_url='login')
def test_view(request, id):
    """отображение теста ?"""
    test = get_object_or_404(Test, pk=id)

    # проверить что записан на курс
    user_subscribe = test.course_element.course.is_subscriber(request.user)
    if not user_subscribe:
        return HttpResponseForbidden('вы не записаны на этот курс')

    active_test_result = test.get_active_test_result(request.user)
    print(test.description)
    context = {
        'test':test,
        'test_description':test.description.split('\n'),

        'finishedTestResults': [ { 'start': r.start, 'end': r.end if r.end else min(r.start + r.test.duration, r.test.end), 'mark': r.evaluate_mark()} for r in test.get_finished_test_results(request.user) ],
        'activeTestResults':active_test_result,
        'activeTestResultsEndTime':min(active_test_result.start + test.duration, test.end) if active_test_result else None,

        'can_start_new_test':test.can_start_new_test(request.user),
        'can_edit':test.can_edit(request.user),
    }
    return render(request, 'LMS/test/view.html', context)

@login_required
def test_action(request, id, result_id, question_id):
    """страница для прохождения теста -"""

    # проверки id, прав пользователя и что запись прохождения активна
    test_result = TestResult.objects.get(id=result_id)
    if test_result.is_finished():
        return HttpResponseForbidden('данное прохождение теста завершено')

    # ответили на вопрос теста
    if request.method == 'POST':
        dict_POST = dict(request.POST)
        question = TestQuestion.objects.get(id=question_id)
        answer = request.POST['str'] if question.answer_type == 'free' else ' '.join(dict_POST['indexes'])
        
        obj, created = TestQuestionAnswer.objects.update_or_create(
            test_result_id=result_id, test_question_id=question_id,
            defaults={'datetime': timezone.now(), 'answer':answer},
        )
        #obj.calc_mark()
        

    # работает с текущей открытой попыткой прохождения теста
    question = TestQuestion.objects.get(id=question_id)
    question_answers = question.answer_values

    if question_answers != '':
        question_answers = question_answers.split('\n')

    context = {
        'test':Test.objects.get(id=id),
        'result_id':result_id,
        'testResult':TestResult.objects.get(id=result_id),
        'question':question,
        'question_answers':question_answers,
        'deadline':min(test_result.test.end, test_result.start + test_result.test.duration),
    }
    return render(request, 'LMS/test/action.html', context)

@login_required(login_url='login')
def test_edit(request, id):
    """страница для редактирование теста -"""
    test = get_object_or_404(Test, pk=id)

    if not test.can_edit(request.user):
        return HttpResponseForbidden('нет прав или нельзя редактировать тест')

    if request.method == 'POST':
        testModelForm = TestModelForm(request.POST, instance=test)

        if testModelForm.is_valid():
            testModelForm.save()
            return redirect(f'/test/{id}')
        else:
            print('invalid')

    testModelForm = TestModelForm(instance=test)
    context = {
        'test_id':id,
        'testModelForm':testModelForm,
        'testQuestionModelForm':TestQuestionModelForm(),
    }
    return render(request, 'LMS/test/edit.html', context)

# deprecate
@require_POST
@login_required
def test_start(request, id, test_result_id=None):
    """начать прохождение теста -"""
    test = get_object_or_404(Test, pk=id)

    # проверить права
    if False:
        return HttpResponseForbidden('нет прав для прохождения теста')

    # запросили продолжить конкретное прохождение
    if test_result_id is not None:
        # если оно недействительно, то ошибка
        testResult = TestResult.objects.get(id=test_result_id)
        if testResult.is_finished():
            raise Http404()
    # иначе создаём новое прохождение
    else:
        testResult = test.start_new_test(request.user)
        if testResult is None:
            raise Http404()

    return redirect(f'/test/{id}/result/{testResult.id}/question/{ test.test_questions.first().id }')

@require_GET
@login_required(login_url='login')
def test_create(request, course_element_id):
    """страница для создания теста"""
    course_element = get_object_or_404(CourseElement, pk=course_element_id)

    # проверка прав
    if not course_element.course.can_edit(request.user):
        return HttpResponseForbidden('нет прав для создания теста')

    context = {
        'course_element_id':course_element_id,
        'testModelForm':TestModelForm(),
        'testQuestionModelForm':TestQuestionModelForm(),
    }
    return render(request, 'LMS/test/create.html', context)


@require_GET
@login_required
def notices_view(request):
    """отображение уведомлений"""
    notices = request.user.notifications.filter(deleted=False).only('id', 'text', 'datetime', 'readed')
    return render(request, 'LMS/user/notices.html', { 'notices': notices })

@require_GET
def files(request, id, filename):
    """доступ к файлам на сервере"""
    file = get_object_or_404(FileStorage, pk=id)

    if file.deleted or filename != file.filename:
        raise Http404('File does not exist')

    # проверка прав
    # есть доступ к файлам которые загрузил в ответ на задание
    # есть доступ к материалам курсов
    # у преподавателя курса есть доступ к загруженным ответам на задания курса
    if not bool(
        file.course_element or
        request.user.is_authenticated and file.owner == request.user or
        request.user.is_authenticated and file.task_answer and file.task_answer.task.course_element.course.owners.filter(id=request.user.id).exists()
    ):
        logger.warning('попытка доступа к файлу без прав')
        return HttpResponseForbidden()

    file_path = os.path.join(settings.MEDIA_ROOT, str(file))
    mime_type, _ = mimetypes.guess_type(file_path)

    try:
        with open(file_path, 'rb') as fin:
            logger.debug(str(fin) + ' ' + str(mime_type))
            return HttpResponse(fin, content_type=mime_type) if mime_type else FileResponse(fin)
    except:
        logger.error('open file exception')
        raise Http404()