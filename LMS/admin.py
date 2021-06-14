from django.contrib import admin

from .models import *


class CourseAdmin(admin.ModelAdmin):
    filter_horizontal = ('owners', 'students', 'excluded', 'groups')
    readonly_fields   = ('id',)
    search_fields     = ('title',)

    list_filter  = ('groups',)
    list_display = ('title',)
    ordering = ('title',)

class CourseElementAdmin(admin.ModelAdmin):
    filter_horizontal = ('files',)
    readonly_fields   = ('id',)

    list_filter  = ('course__title',)
    list_display = ('course', 'title',)
    ordering     = ('course',)

    search_fields       = ('course__title', 'title')
    autocomplete_fields = ('course',)

class TaskAdmin(admin.ModelAdmin):
    list_filter  = ('execute_answer', 'comments_is_on')
    list_display = ('course_element', 'title', 'comments_is_on')
    ordering     = ('title',)

    readonly_fields = ('id',)
    search_fields   = ('title',)
    autocomplete_fields = ('course_element',)

class TaskTestAdmin(admin.ModelAdmin):
    list_filter  = ('task__title',)
    list_display = ('task', 'hidden')
    ordering     = ('task',) # если в модели есть сортировка, то по умолчанию используется она

    readonly_fields = ('id',)
    search_fields   = ('task__title',)
    autocomplete_fields = ('task',)

class TaskTestExecutionAdmin(admin.ModelAdmin):
    list_filter  = ('task_test', 'task_answer', 'execution_result') # task_answer не работает
    list_display = ('task_test', 'task_answer', 'execution_result', 'duration', 'memory_Kbyte')
    ordering     = ('task_test',)

    readonly_fields = ('id',)
    autocomplete_fields = ('task_test', 'task_answer')

class TaskAnswerAdmin(admin.ModelAdmin):
    readonly_fields = ('datetime_load', 'files', 'code', 'id')
    radio_fields    = {'language': admin.VERTICAL}

    list_filter  = ('language',)
    list_display = ('task', 'student', 'language',)
    ordering     = ('task', 'student')

    search_fields   = ('task__title', 'student__username')
    autocomplete_fields = ('task',) # 'user'

class TaskAnswerMarkAdmin(admin.ModelAdmin):
    readonly_fields = ('datetime_evaluate', 'id')
    autocomplete_fields = ('task_answer',) # 'user'

    list_display = ('task_answer', 'teacher', 'mark', 'datetime_evaluate')
    ordering     = ('task_answer',)


class TestAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    search_fields   = ('title',)
    autocomplete_fields = ('course_element',)

    list_filter  = ('course_element__course__title',)
    list_display = ('course_element', 'title', 'start', 'mark_outer', 'number_of_attempts', 'get_questions')
    ordering     = ('course_element', 'start')

    def get_questions(self, obj):
        return TestQuestion.objects.filter(test=obj).count()
    get_questions.short_description = 'кол-во вопросов'

class TestResultAdmin(admin.ModelAdmin):
    readonly_fields = ('start', 'end', 'id')
    search_fields   = ('test__title', 'user__username', 'start')
    autocomplete_fields = ('test', 'user')

    list_display = ('test', 'user', 'start')
    ordering     = ('test', 'user', 'start')

class TestQuestionAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    radio_fields    = {'answer_type': admin.VERTICAL}
    search_fields   = ('question_text',)
    autocomplete_fields = ('test',)

    #list_filter = ('test__title',)
    list_display = ('test',)
    ordering     = ('test',)

class TestQuestionAnswerAdmin(admin.ModelAdmin):
    readonly_fields = ('datetime', 'id')
    autocomplete_fields = ('test_result', 'test_question')

    list_display = ('datetime', 'test_result', 'test_question', 'mark')
    ordering     = ('datetime',)


class NotificationAdmin(admin.ModelAdmin):
    readonly_fields = ('datetime', 'readed', 'deleted', 'id')
    search_fields   = ('user__username',)
    autocomplete_fields = ('user',)

    list_filter  = ('readed',)
    list_display = ('user', 'datetime', 'deleted')

class CommentAdmin(admin.ModelAdmin):
    readonly_fields = ('datetime', 'deleted', 'id')
    autocomplete_fields = ('task', 'user')
    search_fields = ('task__title', 'user__username')

    list_filter  = ('visible',)
    list_display = ('task', 'user', 'datetime', 'visible', 'deleted')

class FileStorageAdmin(admin.ModelAdmin):
    readonly_fields = ('datetime', 'id')
    #autocomplete_fields = ('user',)
    search_fields = ('owner__username', 'filename')
    list_display = ('owner', 'datetime', 'filename', 'file', 'deleted')

class UserDataAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)

    search_fields   = ('user__username',)
    autocomplete_fields = ('user',)



admin.site.register(Course,CourseAdmin)
admin.site.register(CourseElement,CourseElementAdmin)

admin.site.register(Task,TaskAdmin)

admin.site.register(TaskTest,TaskTestAdmin)
admin.site.register(TaskTestExecution,TaskTestExecutionAdmin)

admin.site.register(TaskAnswer,TaskAnswerAdmin)
admin.site.register(TaskAnswerMark,TaskAnswerMarkAdmin)

admin.site.register(Test,TestAdmin)
admin.site.register(TestResult,TestResultAdmin)
admin.site.register(TestQuestion,TestQuestionAdmin)
admin.site.register(TestQuestionAnswer,TestQuestionAnswerAdmin)

admin.site.register(Notification,NotificationAdmin)
admin.site.register(Comment,CommentAdmin)

admin.site.register(FileStorage,FileStorageAdmin)
admin.site.register(UserData,UserDataAdmin)