from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Payment
from courses.models import Course, Enrollment
from django.db.models import Sum
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
import secrets

@login_required
def checkout(request, id):
    course = get_object_or_404(Course, id=id)
    if request.method == 'POST':
        # Generate a truly unique, clean ID
        unique_id = f"EZP-{secrets.token_hex(4).upper()}" 
        
        payment = Payment.objects.create(
            student=request.user.profile,
            course=course,
            amount=course.price,
            payment_id=unique_id, # Use the clean ID
            paid=True
        )
        Enrollment.objects.get_or_create(
            student=request.user.profile,
            course=course
        )
        return redirect('payment_success', payment_id=payment.payment_id)
    return render(request, 'checkout.html', {'course': course})

def payment_success(request, payment_id):
    return render(request, 'success.html', {'payment_id': payment_id})

def payment_cancel(request):
    return render(request, 'cancel.html')

@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, payment_id=payment_id)
    if not request.user.is_staff and payment.student != request.user.profile:
        return redirect('dashboard')

    return render(request, 'receipt.html', {'payment': payment})

def is_admin(user):
    return user.is_staff or user.profile.role == 'admin'

@user_passes_test(is_admin)
def transaction_report(request):
    successful_payments = Payment.objects.filter(paid=True).order_by('-date')
    total_revenue = successful_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'payments': successful_payments,
        'total_revenue': total_revenue,
    }
    return render(request, 'report.html', context)

@staff_member_required
def payment_list(request):
    payments = Payment.objects.all().select_related('student__user', 'course').order_by('date')
    
    total_revenue_data = payments.aggregate(total=Sum('amount'))
    total_revenue = total_revenue_data['total'] or 0
    
    return render(request, 'payment_list.html', {
        'payments': payments,
        'total_revenue': total_revenue
    })