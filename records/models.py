from django.db import models
from users.models import Profile
from courses.models import Course

class Attendance(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.course} - {self.date}"

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    total_marks = models.IntegerField()
    exam_date = models.DateField()

    def __str__(self):
        return self.title

class MCQQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(
        max_length=1, choices=[('A', 'Option A'), ('B', 'Option B'), ('C', 'Option C'), ('D', 'Option D')])

    def __str__(self):
        return f"{self.exam.title} - {self.question_text[:30]}"
    
class ExamResult(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    marks_obtained = models.IntegerField()
    passed = models.BooleanField(default=False)
    ai_review = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student} - {self.exam}"

class Certificate(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_date = models.DateField(auto_now_add=True)
    certificate_code = models.CharField(max_length=100, null=True,blank=True)

    def __str__(self):
        return f"Certificate for {self.student.user.username} - {self.course.title}"