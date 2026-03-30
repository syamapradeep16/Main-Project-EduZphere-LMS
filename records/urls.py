from django.urls import path
from .views import *

urlpatterns = [
    path('attendance/', attendance_list, name='attendance'),
    path('mark-attendance/<int:course_id>/', mark_attendance, name='mark_attendance'),
    path('exams/', exam_list, name='exam_list'),
    path('add-exam/<int:course_id>/', add_exam, name='add_exam'),
    path('add-question/<int:exam_id>/', add_question, name='add_question'),
    path('take-exam/<int:exam_id>/', take_exam, name='take_exam'),
    path('edit-exam/<int:exam_id>/', edit_exam, name='edit_exam'),
    path('view_exam_details/<int:exam_id>/', view_exam_details, name='view_exam_details'),
    path('delete-exam/<int:exam_id>/', delete_exam, name='delete_exam'),
    path('delete-attempt/<int:result_id>/', delete_attempt, name='delete_attempt'),
    path('certificates/', certificates, name='certificates'),
    path('certificate/download/<int:cert_id>/', generate_pdf, name='generate_pdf'),
]
