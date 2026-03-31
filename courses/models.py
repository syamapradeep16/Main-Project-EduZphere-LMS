from django.db import models
from django.contrib.auth.models import User
from users.models import Profile

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profile__role': 'instructor'})
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    thumbnail = models.ImageField(upload_to='course_pics/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200,null=True,blank=True)
    video = models.FileField(upload_to='videos/', blank=True)
    duration = models.IntegerField(help_text="Duration in minutes", default=0)
    content = models.TextField(blank=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
class Enrollment(models.Model):

    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

class LessonCompletion(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'lesson')
