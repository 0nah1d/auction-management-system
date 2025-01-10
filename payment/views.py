from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from sslcommerz_python.payment import SSLCSession
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.conf import settings
from auctions.models import AuctionList, Winner, Bids, User, Payment, ShippingAddress
from django.db.models import Max
from django.utils import timezone
from django.contrib import messages


def initiate_payment(request, auction_id, payment_type='bid'):
    user = get_object_or_404(User, pk=request.user.id)
    auction = get_object_or_404(AuctionList, pk=auction_id)

    # Check if user address is complete
    if not all([user.province, user.city, user.zone, user.address, user.zip_code, user.phone]):
        messages.error(request, "Please complete your address information before proceeding to payment.")
        return redirect('edit_profile')

    # Determine amount based on payment type
    if payment_type == 'bid':
        try:
            Winner.objects.get(bid_win_list=auction, user=user)
        except Winner.DoesNotExist:
            messages.error(request, "You are not the winner of this auction.")
            return redirect('userWinBids')

        winning_bid_amount = Bids.objects.filter(auction=auction).aggregate(Max('bid'))['bid__max']
        if winning_bid_amount is None:
            messages.error(request, "No bids available for this auction.")
            return redirect('userWinBids')

        amount = Decimal(winning_bid_amount)
    elif payment_type == 'buy_now':
        if not auction.buy_now_price:
            messages.error(request, "Buy Now price is not set for this auction.")
            return redirect('auctionDetails', bidid=auction_id)
        amount = Decimal(auction.buy_now_price)
    else:
        messages.error(request, "Invalid payment type.")
        return redirect('userWinBids')

    # Check if payment is already completed
    if Payment.objects.filter(auction=auction, user=user, status="VALID").exists():
        messages.info(request, "You have already paid for this auction.")
        return redirect('userWinBids' if payment_type == 'bid' else 'auctionDetails', bidid=auction_id)

    # SSLCommerz setup
    sslc_store_id = settings.SSLC_STORE_ID
    sslc_store_pass = settings.SSLC_STORE_PASS
    mypayment = SSLCSession(
        sslc_is_sandbox=True,
        sslc_store_id=sslc_store_id,
        sslc_store_pass=sslc_store_pass
    )

    # Set URLs for callbacks
    status_url = request.build_absolute_uri(
        reverse('payment_status')) + f"?auction_id={auction.id}&user_id={user.id}"
    mypayment.set_urls(
        success_url=status_url,
        fail_url=status_url,
        cancel_url=status_url,
        ipn_url=status_url
    )

    # Set product and customer details
    mypayment.set_product_integration(
        total_amount=amount,
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
        return redirect('userWinBids' if payment_type == 'bid' else 'auctionDetails', bidid=auction_id)


def bid_payment(request, auction_id):
    return initiate_payment(request, auction_id, payment_type='bid')


def buy_now_payment(request, auction_id):
    return initiate_payment(request, auction_id, payment_type='buy_now')


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

        if transaction_id and not Payment.objects.filter(transaction_id=transaction_id).exists():
            Payment.objects.create(
                user=request_user,
                auction=auction,
                transaction_id=transaction_id,
                payment_method=payment_method,
                status=status,
                amount=Decimal(amount),
                transaction_date=timezone.now()
            )

            # Create shipping address after successful payment
            ShippingAddress.objects.create(
                user=request_user,
                auction=auction,
                recipient_name=f"{request_user.first_name} {request_user.last_name}",
                phone_number=request_user.phone,
                province=request_user.province,
                city=request_user.city,
                zone=request_user.zone,
                street_address=request_user.address,
                zip_code=request_user.zip_code,
                status='PENDING',
            )

        # Auto-login the user after payment if not authenticated
        if not request.user.is_authenticated:
            from django.contrib.auth import login
            try:
                user = User.objects.get(pk=user_id)
                login(request, user)
            except User.DoesNotExist:
                pass

    return render(request, "payment_status.html", {'user': request.user})
