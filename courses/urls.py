from django.urls import path
from .views import *

urlpatterns = [
    path('courses/', course_list, name='course_list'),
    path('create/',create_course, name='create_course'),
    path('course/<int:id>/',course_detail, name='course_detail'),
    path('edit/<int:id>/',edit_course, name='edit_course'),
    path('delete/<int:id>/',delete_course, name='delete_course'),
    path('enroll/<int:id>/',enroll_course, name='enroll_course'),
    path('student_course/',student_courses, name='student_courses'),
    path('student_list/', student_list, name='student_list'),
    path('course/<int:id>/add-lesson/', add_lesson, name='add_lesson'),
    path('course/<int:course_id>/lesson/edit/<int:lesson_id>/',edit_lesson, name='edit_lesson'),
    path('course/<int:course_id>/lesson/delete/<int:lesson_id>/',delete_lesson, name='delete_lesson'),
    path('course/<int:course_id>/lesson/<int:lesson_id>/', lesson_detail, name='lesson_detail'),

]
