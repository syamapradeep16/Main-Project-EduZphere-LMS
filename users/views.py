import os
from django.http import FileResponse, Http404
from django.conf import settings
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .forms import UserRegisterForm
from .models import Profile,Inquiry
from courses.models import Course, Enrollment,Lesson,LessonCompletion
from records.models import Exam, ExamResult, Attendance, Certificate
from payments.models import Payment
from django.core.mail import send_mail
from django.db.models import Prefetch


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message_content = request.POST.get('message')

        subject = f"New EduZphere Support Inquiry from {name}"
        full_message = f"Message from: {name} ({email})\n\nContent:\n{message_content}"
        Inquiry.objects.create(name=name, email=email, subject=subject, message=message_content)
        try:
            send_mail(subject, full_message, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER])
            messages.success(request, "Your message has been sent! We will contact you shortly.")
        except Exception:
            messages.error(request, "There was an error sending your message. Please try again later.")      
        return redirect('home')
        
    return render(request, 'contact.html')

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            Profile.objects.create(
                user=user,
                role=form.cleaned_data['role'],
                bio=form.cleaned_data['bio']
            )
            messages.success(request, "Account created! You can now login.")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == "POST":
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def profile(request):
    user_profile = request.user.profile
    context = {'profile': user_profile}

    if user_profile.role == 'instructor':
        context['my_courses'] = Course.objects.filter(instructor=request.user)
    
    elif user_profile.role == 'student':
        context['results'] = ExamResult.objects.filter(student=user_profile)
        context['attendance_count'] = Attendance.objects.filter(student=user_profile, present=True).count()
    
    elif user_profile.role == 'admin':
        context['total_users'] = Profile.objects.count()
        context['total_courses'] = Course.objects.count()

    return render(request, 'profile.html', context)

@login_required
def dashboard(request):
    context = {}
    enrolled_courses = []
    payments = []
    my_managed_courses = [] 
    total_student_count = 0 
    attendance_count = 0
    exams_passed = 0
    my_certificates = 0
    progress = 0
    total_lessons = 0
    completed_lessons = 0
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        if request.user.is_staff:
            user_profile = Profile.objects.create(user=request.user, role='admin')
        else:
            return redirect('home')
        
    if user_profile.role == 'admin' or request.user.is_staff:
        context = {
            'total_students': Profile.objects.filter(role='student').count(),
            'total_instructors': Profile.objects.filter(role='instructor').count(),
            'total_courses': Course.objects.count(),
            'total_inquiries': Inquiry.objects.count(),
            'profile': user_profile,
        }
        return render(request, 'admin_dashboard.html', context)

    elif user_profile.role == 'student':
        enrolled_courses = Enrollment.objects.filter(student=user_profile)
        payments = Payment.objects.filter(student=user_profile, paid=True).order_by('-date')
        attendance_count = Attendance.objects.filter(student=user_profile, present=True).count()
        exams_passed = ExamResult.objects.filter(student=user_profile).count()
        my_certificates = Certificate.objects.filter(student=user_profile).count()
        total_lessons = Lesson.objects.filter(course__in=enrolled_courses.values('course')).count()
        completed_lessons = LessonCompletion.objects.filter(student=user_profile).count()

    elif user_profile.role == 'instructor':
        my_managed_courses = Course.objects.filter(instructor=request.user)
        total_student_count = Enrollment.objects.filter(course__in=my_managed_courses).values('student').distinct().count()
        
        if total_lessons > 0:
            progress = (completed_lessons / total_lessons) * 100
            
    context = {
        'profile': user_profile,
        'learning_progress': int(progress),
        'enrolled_courses': enrolled_courses,
        'payments': payments,
        'attendance_count': attendance_count,
        'exams_passed': exams_passed,
        'my_certificates': my_certificates,
        'my_managed_courses': my_managed_courses,
        'total_student_count': total_student_count,
    }       
    return render(request, 'dashboard.html', context)

@login_required
def student_list(request):
    user_profile = request.user.profile
    
    if user_profile.role == 'instructor':
        instructor_courses = Course.objects.filter(instructor=request.user)
        enrollments = Enrollment.objects.filter(course__in=instructor_courses).select_related('student__user', 'course')
    
    elif user_profile.role == 'admin' or request.user.is_staff:
        enrollments = Enrollment.objects.all().select_related('student__user', 'course')
    
    else:
        enrollments = Enrollment.objects.none()

    return render(request, 'student_list.html', {'enrollments': enrollments})

@staff_member_required
def instructor_list(request):
    instructors = Profile.objects.filter(role='instructor').select_related('user')
    all_courses = Course.objects.all()
    
    for instructor in instructors:
        instructor.assigned_courses = Course.objects.filter(instructor=instructor.user)
    
    return render(request, 'instructor_list.html', {
        'instructors': instructors,
        'all_courses': all_courses
    })

@staff_member_required
def assign_course(request, user_id):
    if request.method == "POST":
        course_id = request.POST.get('course_id')
        instructor_user = get_object_or_404(User, id=user_id)
        course = get_object_or_404(Course, id=course_id)
        course.instructor = instructor_user
        course.save()
        messages.success(request, f"Assigned {course.title} to {instructor_user.username}")
    return redirect('instructor_list')

@staff_member_required
def remove_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    instructor_name = course.instructor.username if course.instructor else "Instructor"
    course.instructor = None
    course.save()
    messages.warning(request, f"Removed {course.title} from {instructor_name}")
    return redirect('instructor_list')

@staff_member_required
def system_backup_download(request):
    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    if os.path.exists(db_path):
        return FileResponse(open(db_path, 'rb'), as_attachment=True, filename='eduzphere_backup.sqlite3')
    raise Http404("Database file not found.")

@staff_member_required
def inquiry_list(request):
    inquiries = Inquiry.objects.all().order_by('-created_at')
    
    return render(request, 'inquiry_list.html', {'inquiries': inquiries})