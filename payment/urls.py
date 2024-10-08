from django.urls import path

from .views import *

urlpatterns = [
    # bKash
    path('bkash/create/', create_bkash_payment, name='create_bkash_payment'),
    path('bkash/execute/', execute_bkash_payment, name='execute_bkash_payment'),

    # SSL Commerz
    path('initiate_payment/', initiate_payment, name='paymentPage'),
    path('payment_status/', payment_status, name='payment_status'),
    # path('payment_complete/', )
]
