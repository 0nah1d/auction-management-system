from django.urls import path

from .views import *

urlpatterns = [
    # SSL Commerz
    path('initiate_payment/<int:auction_id>', initiate_payment, name='paymentPage'),
    path('buy_now/<int:auction_id>', buy_now, name='BuyNow'),
    path('payment_status/', payment_status, name='payment_status'),
    # path('payment_complete/', )
]
