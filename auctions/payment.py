from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from sslcommerz_python.payment import SSLCSession
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.conf import settings


def initiate_payment(request):
    # Payment parameters
    amount = Decimal('20.20')  # Example amount
    customer_email = request.POST.get('email', 'johndoe@email.com')

    # Read SSLCommerz credentials from environment variables
    sslc_store_id = settings.SSLC_STORE_ID
    sslc_store_pass = settings.SSLC_STORE_PASS

    # Create SSLCommerz session
    mypayment = SSLCSession(
        sslc_is_sandbox=True,  # Set to False for live
        sslc_store_id=sslc_store_id,
        sslc_store_pass=sslc_store_pass
    )

    # Set URLs for callbacks
    status_url = request.build_absolute_uri(reverse('payment_status'))
    mypayment.set_urls(success_url=status_url, fail_url=status_url, cancel_url=status_url, ipn_url=status_url)

    # Set product integration details
    mypayment.set_product_integration(
        total_amount=amount,
        currency='BDT',
        product_category='clothing',
        product_name='demo-product',
        num_of_item=2,
        shipping_method='YES',
        product_profile='None'
    )

    # Set customer information
    mypayment.set_customer_info(
        name='John Doe',
        email=customer_email,
        address1='demo address',
        address2=None,
        city='Dhaka',
        postcode='1207',
        country='Bangladesh',
        phone='01711111111'
    )

    # Set shipping information
    mypayment.set_shipping_info(
        shipping_to='demo customer',
        address='demo address',
        city='Dhaka',
        postcode='1209',
        country='Bangladesh'
    )

    # Initiate payment
    response_data = mypayment.init_payment()
    print(response_data)

    # Check if the response indicates success
    if response_data['status'] == 'SUCCESS':
        # Redirect the user to the payment gateway
        return redirect(response_data['GatewayPageURL'])
    else:
        return redirect('paymentPage')


@csrf_exempt
def payment_status(request):
    if request.method == 'post' or request.method == 'POST':
        print(request.POST)

    return render(request, 'payment_status.html')
