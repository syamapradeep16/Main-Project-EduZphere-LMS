from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Attendance, Exam, ExamResult, Certificate
from courses.models import Course, Enrollment
from .forms import ExamForm, MCQQuestionForm
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
import ollama
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML, CSS

@login_required
def attendance_list(request):
    user = request.user
    today = timezone.now().date()
    user_profile = getattr(user, 'profile', None)
    is_instructor = Course.objects.filter(instructor=user).exists()
    is_admin = user.is_staff or (user_profile and user_profile.role == 'admin')
    if request.method == "POST":
        if is_instructor or is_admin:
            course_id = request.POST.get('course_id')
            course = get_object_or_404(Course, id=course_id)
     
            if is_admin or course.instructor == user:
                enrollments = Enrollment.objects.filter(course=course)
                
                for enr in enrollments:
                    status = request.POST.get(f'status_{enr.student.id}')
                    
                    if status:
                        Attendance.objects.update_or_create(
                            student=enr.student,
                            course=course,
                            date=today,
                            defaults={'present': (status == 'present')}
                        )          
                messages.success(request, f"Attendance for {course.title} has been updated.")
                return redirect('attendance')
            else:
                messages.error(request, "You do not have permission to mark attendance for this course.")
                return redirect('attendance')
        return redirect('attendance')

    marking_data = None
    attendance_records = []
    all_enrollments = []

    if is_admin:
        marking_data = Course.objects.all()
        attendance_records = Attendance.objects.all().order_by('-date')
        all_enrollments = Enrollment.objects.all().select_related('student__user', 'course')

    elif is_instructor:
        marking_data = Course.objects.filter(instructor=user)
        attendance_records = Attendance.objects.filter(course__in=marking_data).order_by('-date')
        nrollments = Enrollment.objects.filter(course__in=marking_data)

    elif user_profile and user_profile.role == 'student':
        marking_data = None
        attendance_records = Attendance.objects.filter(student=user_profile).order_by('-date')
    
    else:
        messages.warning(request, "Your account role is not fully configured.")
        return redirect('dashboard')

    context = {
        'marking_data': marking_data,
        'attendance_records': attendance_records,
        'all_enrollments': all_enrollments,
        'today': today,
    }
    return render(request, 'attendance.html', context)

@login_required
def mark_attendance(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if not (request.user.is_staff or course.instructor == request.user):
        messages.error(request, "You do not have permission to mark attendance for this course.")
        return redirect('attendance')
    enrollments = Enrollment.objects.filter(course=course)
    today = timezone.now().date()

    if request.method == "POST":
        for enrollment in enrollments:
            status = request.POST.get(f'status_{enrollment.student.id}')
            is_present = (status == 'present')
           
            Attendance.objects.update_or_create(
                student=enrollment.student,
                course=course,
                date=today,
                defaults={'present': is_present}
            )
        messages.success(request, f"Attendance for {today} has been saved.")
        return redirect('attendance')

    return render(request, 'mark_attendance.html', {
        'course': course, 
        'enrollments': enrollments, 
        'today': today
    })
@login_required
def exam_list(request):
    user = request.user

    if user.is_staff or Course.objects.filter(instructor=user).exists():

        exams = Exam.objects.filter(course__instructor=user).select_related('course')
        all_results = ExamResult.objects.filter(exam__course__instructor=user).select_related('exam', 'student__user')
    
        return render(request, 'instructor_exams.html', {'exams': exams, 'all_results': all_results})
    user_profile = user.profile
    enrolled_courses = Enrollment.objects.filter(student=user_profile).values_list('course', flat=True)
    exams = Exam.objects.filter(course__id__in=enrolled_courses)
    results = ExamResult.objects.filter(student=user_profile).select_related('exam')
    
    return render(request, 'exam_list.html', {'exams': exams, 'results': results})

@login_required
def add_exam(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if course.instructor != request.user:
        messages.error(request, "You do not have permission to add exams to this course.")
        return redirect('course_list')

    if request.method == "POST":
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.course = course 
            exam.save()
            
            messages.success(request, f"Exam '{exam.title}' added to {course.title}")
            return redirect('add_question', exam_id=exam.id) 
    else:
        form = ExamForm()

    return render(request, 'add_exam.html', {'form': form, 'course': course})

@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all() 
    user_profile = request.user.profile

    if ExamResult.objects.filter(student=user_profile, exam=exam).exists():
        messages.warning(request, "You have already completed this exam.")
        return redirect('exam_list')

    if request.method == "POST":
        correct_answers_count = 0
        total_questions = questions.count()

        for question in questions:
            student_answer = request.POST.get(f'question_{question.id}')
            if student_answer == question.correct_option:
                correct_answers_count += 1

        score = (correct_answers_count / total_questions * exam.total_marks) if total_questions > 0 else 0
        passed = score >= (exam.total_marks * 0.4)
        result = ExamResult.objects.create(
            student=user_profile,
            exam=exam,
            marks_obtained=int(score),
            passed=passed
        )
        try:
            prompt = (
                f"As an AI Tutor for the course '{exam.course.title}', "
                f"provide a motivating 2-line feedback for a student who scored {int(score)}/{exam.total_marks} "
                f"on the '{exam.title}' exam. If they scored low, suggest focusing on Python fundamentals."
            )

            response = ollama.chat(model='llama3.2',messages=[{'role': 'user', 'content': prompt}])
            result.ai_review = response['message']['content']
            
        except Exception as e:
            result.ai_review = f"System Error: {str(e)}. Ensure Ollama is running at localhost:11434"
            print(f"Ollama Connection Error: {e}")

        result.save()
        messages.success(request, "Exam submitted and analyzed.")
        if passed:
            Certificate.objects.get_or_create(
                student=request.user.profile,
                course=exam.course
            )
            messages.success(request, f"Congratulations! You passed and earned a certificate for {exam.course.title}!")
        else:
            messages.warning(request, "You did not reach the passing score. Try reviewing the material and try again.")
        
    return render(request, 'take_exam.html', {'exam': exam, 'questions': questions})

@login_required
def add_question(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    current_question_count = exam.questions.count()
    next_question_number = current_question_count + 1

    if request.method == "POST":
        form = MCQQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.save()
            
            if 'save_and_add' in request.POST:
                messages.success(request, f"Question {next_question_number} added!")
                return redirect('add_question', exam_id=exam.id)
            
            messages.success(request, "Exam finalized successfully.")
            return redirect('course_detail', id=exam.course.id)
    else:
        form = MCQQuestionForm()
        
    context = {
        'form': form, 
        'exam': exam,
        'q_number': next_question_number,
        'total_existing': current_question_count
    }
    return render(request, 'add_question.html', context)

@login_required
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if exam.course.instructor != request.user:
        messages.error(request, "Access Denied.")
        return redirect('exam_list')

    if request.method == "POST":
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam details updated successfully.")
            return redirect('exam_list')
    else:
        form = ExamForm(instance=exam)
    
    return render(request, 'edit_exam.html', {'form': form, 'exam': exam})

@login_required
def view_exam_details(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    return render(request, 'view_exam.html', {'exam': exam, 'questions': questions})

@login_required
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if exam.course.instructor != request.user:
        messages.error(request, "You do not have permission to delete this exam.")
        return redirect('exam_list')

    if request.method == "POST":
        exam.delete()
        messages.success(request, "Exam deleted successfully.")
        return redirect('exam_list')

    return render(request, 'delete_exam.html', {'exam': exam})

@login_required
def delete_attempt(request, result_id):
    result = get_object_or_404(ExamResult, id=result_id)
    
    if result.exam.course.instructor == request.user or request.user.is_staff:
        result.delete()
        messages.success(request, "Student attempt deleted successfully. They can now retake the exam.")
    else:
        messages.error(request, "You do not have permission to delete this attempt.")
        
    return redirect('exam_list')

@login_required
def certificates(request):
    user_certs = Certificate.objects.filter(student=request.user.profile).select_related('course')
    return render(request, 'certificates.html', {'certificates': user_certs})

@login_required
def generate_pdf(request, cert_id):
    cert = get_object_or_404(Certificate, id=cert_id, student__user=request.user)
    html_string = render_to_string('certificate_pdf.html', {'cert': cert})
    
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf(presentational_hints=True)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="EduZphere_{cert.id}.pdf"'
    return response