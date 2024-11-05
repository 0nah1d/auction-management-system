from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from sslcommerz_python.payment import SSLCSession
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.conf import settings
import requests
from auctions.models import AuctionList, Winner, Bids, User, Payment
from django.db.models import Max
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages


def initiate_payment(request, auction_id):
    user = get_object_or_404(User, pk=request.user.id)
    auction = get_object_or_404(AuctionList, pk=auction_id)

    # Extract address information
    province = user.province
    city = user.city
    zone = user.zone
    address = user.address
    zipcode = user.zip_code
    phone = user.phone

    # Check if any of the required fields are empty
    if not province or not city or not zone or not address or not zipcode or not phone:
        messages.error(request, "Please complete your address information before proceeding to payment.")
        return redirect('edit_profile')

    try:
        winner = Winner.objects.get(bid_win_list=auction, user=user)
    except Winner.DoesNotExist:
        messages.error(request, "You are not the winner of this auction.")
        return redirect('userWinBids')

    winning_bid_amount = Bids.objects.filter(auction=auction).aggregate(Max('bid'))['bid__max']
    if winning_bid_amount is None:
        messages.error(request, "No bids available for this auction.")
        return redirect('userWinBids')

    amount = Decimal(winning_bid_amount)

    payments = Payment.objects.filter(auction=auction, user=user)

    if any(payment.status == "VALID" for payment in payments):
        messages.info(request, "You have already paid for this auction.")
        return redirect('userWinBids')

    # SSLCommerz credentials from settings
    sslc_store_id = settings.SSLC_STORE_ID
    sslc_store_pass = settings.SSLC_STORE_PASS

    # Create SSLCommerz session
    mypayment = SSLCSession(
        sslc_is_sandbox=True,
        sslc_store_id=sslc_store_id,
        sslc_store_pass=sslc_store_pass
    )

    # Set URLs for callbacks, including auction and user IDs
    status_url = request.build_absolute_uri(
        reverse('payment_status')) + f"?auction_id={auction.id}&user_id={user.id}"
    mypayment.set_urls(
        success_url=status_url,
        fail_url=status_url,
        cancel_url=status_url,
        ipn_url=status_url
    )

    # Set product integration details
    mypayment.set_product_integration(
        total_amount=amount,
        currency='BDT',
        product_category=auction.categories,
        product_name=auction.title,
        num_of_item=1,
        shipping_method='YES',
        product_profile='None',
    )

    # Set customer information
    mypayment.set_customer_info(
        name=f"{user.first_name} {user.last_name}",
        email=user.email,
        address1=f"{user.city}, {user.zone}, {user.address}",
        address2=None,
        city=user.province,
        postcode=user.zip_code,
        country='Bangladesh',
        phone=user.phone
    )

    # Set shipping information
    mypayment.set_shipping_info(
        shipping_to=f"{user.first_name} {user.last_name}",
        address=f"{user.city}, {user.zone}, {user.address}",
        city=user.province,
        postcode=user.zip_code,
        country='Bangladesh'
    )

    # Initiate payment
    response_data = mypayment.init_payment()

    if response_data['status'] == 'SUCCESS':
        return redirect(response_data['GatewayPageURL'])
    else:
        messages.error(request, "Payment initiation failed. Please try again.")
        return redirect('userWinBids')


def buy_now(request, auction_id):
    auction = get_object_or_404(AuctionList, pk=auction_id)
    user = get_object_or_404(User, pk=request.user.id)

    # Extract address information
    province = user.province
    city = user.city
    zone = user.zone
    address = user.address
    zipcode = user.zip_code
    phone = user.phone

    # Check if any of the required fields are empty
    if not province or not city or not zone or not address or not zipcode or not phone:
        messages.error(request, "Please complete your address information before proceeding to payment.")
        return redirect('edit_profile')

    payments = Payment.objects.filter(auction=auction)

    if any(payment.status == "VALID" for payment in payments):
        messages.info(request, "Already paid for this auction.")
        return redirect('auctionDetails', bidid=auction_id)

    # SSLCommerz credentials from settings
    sslc_store_id = settings.SSLC_STORE_ID
    sslc_store_pass = settings.SSLC_STORE_PASS

    # Create SSLCommerz session
    mypayment = SSLCSession(
        sslc_is_sandbox=True,
        sslc_store_id=sslc_store_id,
        sslc_store_pass=sslc_store_pass
    )

    # Set URLs for callbacks, including auction and user IDs
    status_url = request.build_absolute_uri(
        reverse('payment_status')) + f"?auction_id={auction.id}&user_id={user.id}"
    mypayment.set_urls(
        success_url=status_url,
        fail_url=status_url,
        cancel_url=status_url,
        ipn_url=status_url
    )

    # Set product integration details
    mypayment.set_product_integration(
        total_amount=auction.buy_now_price,
        currency='BDT',
        product_category=auction.categories,
        product_name=auction.title,
        num_of_item=1,
        shipping_method='YES',
        product_profile='None',
    )

    mypayment.set_customer_info(
        name=f"{user.first_name} {user.last_name}",
        email=user.email,
        address1=f"{user.city}, {user.zone}, {user.address}",
        address2=None,
        city=user.province,
        postcode=user.zip_code,
        country='Bangladesh',
        phone=user.phone
    )

    # Set shipping information
    mypayment.set_shipping_info(
        shipping_to=f"{user.first_name} {user.last_name}",
        address=f"{user.city}, {user.zone}, {user.address}",
        city=user.province,
        postcode=user.zip_code,
        country='Bangladesh'
    )

    # Initiate payment
    response_data = mypayment.init_payment()

    if response_data['status'] == 'SUCCESS':
        return redirect(response_data['GatewayPageURL'])
    else:
        messages.error(request, "Payment initiation failed. Please try again.")
        return redirect('auctionDetails', bidid=auction_id)


@csrf_exempt
def payment_status(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('tran_id')
        status = request.POST.get('status')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('card_issuer')

        auction_id = request.GET.get('auction_id')
        user_id = request.GET.get('user_id')

        auction = get_object_or_404(AuctionList, pk=auction_id)
        request_user = get_object_or_404(User, pk=user_id)

        if request_user and auction and status and amount and payment_method and transaction_id:
            Payment.objects.create(
                user=request_user,
                auction=auction,
                transaction_id=transaction_id,
                payment_method=payment_method,
                status=status,
                amount=Decimal(amount),
                transaction_date=timezone.now()
            )

        user = request.user
        if not user.is_authenticated and user_id:
            try:
                user = User.objects.get(pk=user_id)
                from django.contrib.auth import login
                login(request, user)
            except User.DoesNotExist:
                user = None
    return render(request, "payment_status.html", {'user': request.user})
