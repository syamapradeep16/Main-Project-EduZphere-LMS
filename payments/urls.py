from django.urls import path
from .views import *

urlpatterns = [

    path('checkout/<int:id>/',checkout, name='checkout'),
    path('success/<str:payment_id>/', payment_success, name='payment_success'),
    path('cancel/',payment_cancel, name='payment_cancel'),
    path('receipt/<str:payment_id>/',payment_receipt, name='payment_receipt'),
    path('reports/', transaction_report, name='transaction_report'),
    path('summary/',payment_list, name='payment_list'),

]