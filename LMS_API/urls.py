from django.urls import path

from rest_framework.routers import DefaultRouter # SimpleRouter

from .viewsets import (
    CourseViewSet,
    CourseElementViewSet,
    TaskViewSet,
    TaskTestViewSet,
    TaskAnswerViewSet,
    TestViewSet,
    #TestResultViewSet,
    TestQuestionViewSet,
    TestQuestionAnswerViewSet,
    NotificationViewSet,
    CommentViewSet,
)
from .views import (
    CurrentUserView,
    CurrentUserDataView,
    CourseSubscribeView,
    CourseSubscribersView,
    TaskAnswerEvaluateView,
    TestCreateView,
    TestResultListView,
    TestResultCreateView,
    TestResultCompleteView,
    TestResultEvaluateView,
    UploadFilesCourseElementView,
    UploadFilesTaskView,
    UploadCodeTaskView,
    DeleteFileView,
)

router = DefaultRouter()
#router.register(r'course', CourseViewSet)
#router.register(r'course-element', CourseElementViewSet)
#router.register(r'task', TaskViewSet)
router.register(r'task-test', TaskTestViewSet)
router.register(r'task-answer', TaskAnswerViewSet)
#router.register(r'test-result', TestResultViewSet)
#router.register(r'test-question', TestQuestionViewSet)
router.register(r'notification', NotificationViewSet)
router.register(r'comment', CommentViewSet)

urlpatterns = router.urls + [
    path('course/', CourseViewSet.as_view({'get': 'list'})),
    path('course/<int:pk>/', CourseViewSet.as_view({'get': 'retrieve', 'put': 'update'})),

    path('course-element/', CourseElementViewSet.as_view({'post': 'create'})),
    path('course-element/<int:pk>/', CourseElementViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('current_user/', CurrentUserView.as_view()),
    path('current_user_data/', CurrentUserDataView.as_view()),
    path('course_subscribe/', CourseSubscribeView.as_view()),
    path('course_subscribers/<int:pk>/', CourseSubscribersView.as_view()),
    path('course-element-upload-files/<int:pk>/', UploadFilesCourseElementView.as_view()),
    path('task/', TaskViewSet.as_view({'post': 'create'})),
    path('task/<int:pk>/', TaskViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('task-upload-code/<int:pk>/', UploadCodeTaskView.as_view()),
    path('task-upload-files/<int:pk>/', UploadFilesTaskView.as_view()),
    path('task-answer-evaluate/<int:pk>/', TaskAnswerEvaluateView.as_view()),
    path('test/', TestCreateView.as_view()),
    path('test/<int:pk>/', TestViewSet.as_view({'get': 'retrieve', 'delete': 'destroy', 'patch': 'partial_update'})),
    path('test-question/', TestQuestionViewSet.as_view({'post': 'create'})),
    path('test-question/<int:pk>/', TestQuestionViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path('test-question-answer/<int:pk>/', TestQuestionAnswerViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'})),
    path('test-result-list/', TestResultListView.as_view()),
    path('test-result-create/', TestResultCreateView.as_view()),
    path('test-result-complete/<int:pk>/', TestResultCompleteView.as_view()),
    path('test-result-evaluate/<int:pk>/', TestResultEvaluateView.as_view()),
    path('file-delete/<int:pk>/', DeleteFileView.as_view()),
]