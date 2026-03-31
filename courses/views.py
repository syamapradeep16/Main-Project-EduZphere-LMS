from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Lesson, Enrollment
from django.contrib.auth.decorators import login_required
from .forms import CourseForm,LessonForm
from django.contrib import messages
from payments.models import Payment
from records.models import Exam, ExamResult,Attendance
from django.utils import timezone

@login_required
def create_course(request):
    if request.user.profile.role != 'instructor':
        return redirect('course_list')

    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            return redirect('course_list')
    else:
        form = CourseForm()
    return render(request, 'create_course.html', {'form': form})

@login_required
def edit_course(request, id):
    course = get_object_or_404(Course, id=id)
    if course.instructor != request.user:
        return redirect('course_list')

    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'edit_course.html', {'form': form, 'course': course})

@login_required
def delete_course(request, id):
    course = get_object_or_404(Course, id=id)

    if course.instructor == request.user:
        course.delete()
        messages.success(request, "Course deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this course.")
    return redirect('course_list')

@login_required
def course_list(request):
    if request.user.profile.role == 'instructor':
        courses = Course.objects.filter(instructor=request.user).order_by('-created_at')
    else:
        courses = Course.objects.all().order_by('-created_at')
        
    return render(request, 'course_list.html', {'courses': courses})

def course_detail(request, id):
    course = get_object_or_404(Course, id=id)
    lessons = course.lessons.all()
    exams = Exam.objects.filter(course=course)

    attempted_exam_ids = []
    if request.user.is_authenticated:
        attempted_exam_ids = ExamResult.objects.filter(student=request.user.profile, exam__course=course).values_list('exam_id', flat=True)

    is_enrolled = False
    is_instructor = False
    if request.user.is_authenticated:
        if course.instructor == request.user:
            is_instructor = True
        enrolled_check = Enrollment.objects.filter(student=request.user.profile, course=course).exists()
        payment_check = Payment.objects.filter(student=request.user.profile, course=course, paid=True).exists()
        
        if enrolled_check or payment_check:
            is_enrolled = True
    context = {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'is_instructor': is_instructor,
        'exams': exams,
        'attempted_exam_ids': attempted_exam_ids,
    }
    return render(request, 'course_detail.html', context)

@login_required
def enroll_course(request,id):
    course = get_object_or_404(Course, id=id)
    student_profile = request.user.profile
    already_enrolled = Enrollment.objects.filter(student=student_profile, course=course).exists()

    if already_enrolled:
        messages.info(request, f"You are already enrolled in {course.title}.")
        return redirect('dashboard')

    count = Enrollment.objects.get_or_create(student=student_profile, course=course)
    Payment.objects.get_or_create(student=student_profile,course=course,amount=course.price,paid=True)

    messages.success(request, f"Successfully enrolled in {course.title}!")
    return redirect('dashboard')

@login_required
def student_courses(request):
    user_profile = request.user.profile

    my_enrolled_items = Payment.objects.filter(student=user_profile, paid=True).select_related('course')
    courses = [item.course for item in my_enrolled_items]

    return render(request, 'student_courses.html', {'courses': courses})

@login_required
def student_list(request):
    user = request.user
    instructor_courses = Course.objects.filter(instructor=user)
    selected_course_id = request.GET.get('course')
    enrollments = Enrollment.objects.filter(course__instructor=user)
    
    if selected_course_id:
        enrollments = enrollments.filter(course_id=selected_course_id)
        
    context = {
        'enrollments': enrollments,
        'instructor_courses': instructor_courses,
        'selected_course': selected_course_id,
    }
    return render(request, 'student_list.html', context)

@login_required
def add_lesson(request,id):
    course = get_object_or_404(Course, id=id)
    
    if course.instructor != request.user:
        messages.error(request, "Access Denied.")
        return redirect('course_list')

    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, f"New lesson '{lesson.title}' added!")
            return redirect('course_detail', id=course.id)
    else:
        form = LessonForm()

    return render(request, 'add_lesson.html', {'form': form, 'course': course})
@login_required
def edit_lesson(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Security: Only the course owner can edit
    if course.instructor != request.user:
        messages.error(request, "Access Denied.")
        return redirect('course_detail', id=course.id)

    if request.method == "POST":
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lesson '{lesson.title}' updated!")
            return redirect('course_detail', id=course.id)
    else:
        form = LessonForm(instance=lesson)

    return render(request, 'edit_lesson.html', {'form': form, 'course': course, 'lesson': lesson})

@login_required
def delete_lesson(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    if course.instructor == request.user:
        lesson.delete()
        messages.success(request, "Lesson deleted successfully.")
    else:
        messages.error(request, "Unauthorized action.")
        
    return redirect('course_detail', id=course.id)

@login_required
def lesson_detail(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    user_profile = request.user.profile
    today = timezone.now().date()
    
    is_enrolled = Enrollment.objects.filter(student=request.user.profile, course=course).exists()
    is_instructor = (course.instructor == request.user)

    if is_instructor or is_enrolled:
        if user_profile.role == 'student':
            Attendance.objects.update_or_create(
                student=user_profile,
                course=lesson.course,
                date=today,
                defaults={'present': True}
            )
        lessons = Lesson.objects.filter(course=lesson.course).order_by('id')
        return render(request, 'lesson_detail.html', {'lesson': lesson, 'course': course})
    
    messages.warning(request, "You must be enrolled to watch this lesson.")
    return redirect('course_detail', id=course.id)

def workshops(request):
    return render(request, 'workshops.html')

def workshop_action(request, action_type, title):
    context = {
        'action_type': action_type,
        'title': title.replace('-', ' '),
    }
    return render(request, 'workshop_action.html', context)