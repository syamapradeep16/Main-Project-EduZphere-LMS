import uuid
from django.db import models
from users.models import Profile
from courses.models import Course

class Payment(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_id = models.CharField(max_length=200, unique=True,blank=True) 
    paid = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title}"
    
    def save(self,*args,**kwargs):
        if not self.payment_id:
            self.payment_id = f"PAY-{uuid.uuid4()}"
        super().save(*args,**kwargs)