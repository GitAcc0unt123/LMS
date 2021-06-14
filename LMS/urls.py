from django.urls import path
from . import views

urlpatterns = [
    # https://docs.djangoproject.com/en/3.2/topics/auth/default/#module-django.contrib.auth.views
    path('login', views.loginView, name='login'),
    path('logout', views.logoutView, name='logout'),
    path('registration', views.registration),
    #path('reset_password', views.reset_password),
    path('update_password', views.update_password),

    path('privacy', views.privacy),
    path('about', views.about),
    path('faq', views.faq),

    path('settings', views.user_settings),
    path('update_settings', views.update_settings), # deprecate?

    path('marks', views.user_marks),
    path('notices', views.notices_view), # список уведомлений пользователя
    path('user_courses', views.user_courses),

    # курсы создаются/удаляются в админке сайта
    path('', views.courses, name = 'home'), # все курсы
    path('course/<int:id>', views.course_view), # подробно курс
    path('course/<int:id>/edit', views.course_edit), # редактирование курса

    path('task/<int:id>', views.task_view), # подробно задание
    path('task/<int:id>/edit', views.task_edit), # редактирование задания
    path('task/<int:id>/evaluate', views.task_evaluate), # оценивание работ с ручной проверкой
    path('task/<int:id>/tests', views.task_tests), # создание и удаление тестов автоматической задачи
    path('task/create/<int:course_element_id>', views.task_create), # создание задания

    path('test/<int:id>', views.test_view), # общая инфа по тесту
    #path('test/<int:id>/edit', views.test_edit), # редактирование теста
    #path('test/<int:id>/evaluate', views.test_view), # ручное оценивание тестов
    path('test/<int:id>/action/<int:test_result_id>', views.test_view), # страница для прохождения теста
    path('test/create/<int:course_element_id>', views.test_create), # создания теста
    path('test/<int:id>/start', views.test_start), # начать тест

    path('files/<int:id>/<str:filename>', views.files),

    ############################################################################
    # deprecate
    #path('comment_add/<int:task_id>', views.comment_add), # create comment
    path('course/<int:id>/add_course_element', views.course_element_create), # create course element

    # deprecate 
    path('test/<int:id>/start/<int:test_result_id>', views.test_start), # начать тест
    path('test/<int:id>/result/<int:result_id>', views.test_action), # прохождение теста
    path('test/<int:id>/result/<int:result_id>/question/<int:question_id>', views.test_action), # прохождение теста
]