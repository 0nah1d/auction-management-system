from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from sslcommerz_python.payment import SSLCSession
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.conf import settings
import requests
from auctions.models import AuctionList, Winner, Bids, User
from django.db.models import Max
from django.http import HttpResponseForbidden


def initiate_payment(request, auction_id):
    user = request.user
    auction = get_object_or_404(AuctionList, pk=auction_id)

    try:
        winner = Winner.objects.get(bid_win_list=auction, user=user)
    except Winner.DoesNotExist:
        return HttpResponseForbidden("You are not the winner of this auction.")

    winning_bid_amount = Bids.objects.filter(auction=auction).aggregate(Max('bid'))['bid__max']

    if winning_bid_amount is None:
        return HttpResponseForbidden("No bids available for this auction.")

    amount = Decimal(winning_bid_amount)

    if winner:
        sslc_store_id = settings.SSLC_STORE_ID
        sslc_store_pass = settings.SSLC_STORE_PASS

        mypayment = SSLCSession(
            sslc_is_sandbox=True,
            sslc_store_id=sslc_store_id,
            sslc_store_pass=sslc_store_pass
        )

        # Set URLs for callbacks with auction_id and user_id
        status_url = request.build_absolute_uri(
            reverse('payment_status')) + f"?auction_id={auction.id}&user_id={user.id}"
        mypayment.set_urls(
            success_url=status_url,
            fail_url=status_url,
            cancel_url=status_url,
            ipn_url=status_url
        )

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
            address1=f"{user.address.city}, {user.address.zone}, {user.address.address}",
            address2=None,
            city=user.address.province,
            postcode=user.address.zip_code,
            country='Bangladesh',
            phone=user.address.phone
        )

        mypayment.set_shipping_info(
            shipping_to=f"{user.first_name} {user.last_name}",
            address=f"{user.address.city}, {user.address.zone}, {user.address.address}",
            city=user.address.province,
            postcode=user.address.zip_code,
            country='Bangladesh'
        )

        # Initiate payment
        response_data = mypayment.init_payment()

        if response_data['status'] == 'SUCCESS':
            return redirect(response_data['GatewayPageURL'])
        else:
            return redirect('paymentPage')
    else:
        return HttpResponseForbidden("You are not the winner of this auction.")


@csrf_exempt
def payment_status(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('tran_id')
        status = request.POST.get('status')
        amount = request.POST.get('amount')
        payment_by = request.POST.get('card_issuer')

        auction_id = request.GET.get('auction_id')
        user_id = request.GET.get('user_id')

        user = request.user
        if not user.is_authenticated and user_id:
            try:
                user = User.objects.get(pk=user_id)
                from django.contrib.auth import login
                login(request, user)
            except User.DoesNotExist:
                user = None

        print("Transaction ID:", transaction_id)
        print("Amount:", amount)
        print("Status:", status)
        print("Payment by:", payment_by)
        print("Auction ID:", auction_id)
        print("User ID:", user_id)
        print("Authenticated User:", request.user)


    return render(request, "payment_status.html", {'user': request.user})


# auction = get_object_or_404(AuctionList, pk=auction_id)
# user = get_object_or_404(User, pk=user_id)

# payment = Payment.objects.create(
#     user=user,
#     auction=auction,
#     transaction_id=transaction_id,
#     status=status,
#     amount=Decimal(amount),
#     transaction_date=timezone.now()
# )
