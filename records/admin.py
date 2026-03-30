from django.contrib import admin
from .models import Attendance, Exam, MCQQuestion, ExamResult, Certificate

admin.site.register(Attendance)
admin.site.register(Exam)
admin.site.register(MCQQuestion)
admin.site.register(ExamResult)
admin.site.register(Certificate)