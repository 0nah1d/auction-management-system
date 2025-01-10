from django.urls import path

from .views import *

urlpatterns = [
    # SSL Commerz
    path('initiate_payment/<int:auction_id>', bid_payment, name='paymentPage'),
    path('buy_now/<int:auction_id>', buy_now_payment, name='BuyNow'),
    path('payment_status/', payment_status, name='payment_status'),
    # path('payment_complete/', )
]
