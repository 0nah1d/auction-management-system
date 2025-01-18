from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from auctions.models import AuctionList
from .models import BidAssistant, Notification
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils.timezone import now, make_aware, get_default_timezone
from django.contrib import messages
from django.http import JsonResponse
from django.core.serializers import serialize
from django.shortcuts import redirect
from auctions.models import Bids
import json


@login_required(login_url='login')
@csrf_exempt
def bid_assistant(request, auction_id):
    try:
        auction = get_object_or_404(AuctionList, pk=auction_id)

        if request.method == 'GET':
            # Retrieve current max bid for the user
            bid_ass = BidAssistant.objects.filter(user=request.user, auction=auction).first()
            if bid_ass:
                return JsonResponse({'max_bid': bid_ass.max_bid}, status=200)
            return JsonResponse({'max_bid': None}, status=200)

        elif request.method == 'POST':
            # Handle setting or updating the max bid
            data = json.loads(request.body)
            max_bid_amount = data.get('max_bid')

            if max_bid_amount is None or not isinstance(max_bid_amount, (int, float)) or max_bid_amount <= 0:
                return JsonResponse({'message': 'Invalid max_bid value. It must be a positive number.'}, status=400)

            if max_bid_amount < auction.get_highest_bid():
                return JsonResponse({'message': 'The amount must be higher than the current highest bid.'}, status=400)

            if auction.user == request.user:
                return JsonResponse({'message': "You cannot bid on your own auction."})

            expire_date = auction.expire_date
            current_time = now()
            if not expire_date.tzinfo:
                expire_date = make_aware(expire_date, get_default_timezone())

                # Check if the auction has expired
            if current_time > expire_date:
                return JsonResponse({'message': "Sorry, the auction for this listing has expired."})

            # Check if a BidAssistant entry already exists
            bid_ass, created = BidAssistant.objects.update_or_create(
                user=request.user,
                auction=auction,
                defaults={'max_bid': max_bid_amount},
            )

            if created:
                return JsonResponse({'message': 'Bid Assistant set successfully.'}, status=201)
            return JsonResponse({'message': 'Bid Assistant updated successfully.'}, status=200)

        else:
            return JsonResponse({'message': 'Invalid HTTP method'}, status=405)

    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON payload.'}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'An unexpected error occurred: {str(e)}'}, status=500)


@login_required(login_url='login')
def bid_assistant_details(request, auction_id):
    all_bids = Bids.objects.filter(auction__id=auction_id, user=request.user).order_by('-created_at')
    bid_details = [
        {
            'bid': bid.bid,
            'created_at': bid.created_at.strftime('%Y-%m-%d %I:%M:%S %p')
        }
        for bid in all_bids
    ]
    return JsonResponse({'bids': bid_details}, safe=False)


@login_required(login_url='login')
def assistant_info(request):
    user = request.user
    profile_picture_url = None
    if hasattr(user, 'profile_picture') and user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    set_bids = BidAssistant.objects.filter(user=user)

    # Pagination
    paginator = Paginator(set_bids, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "assistant_information.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'bids': page_obj,
        'total': paginator.count
    })


@login_required(login_url='login')
def bid_assistant_update(request, auction_id):
    if request.method == 'POST':
        max_bid_amount = request.POST.get('max_bid')
        bid_ass = BidAssistant.objects.filter(user=request.user, auction__id=auction_id).first()
        if bid_ass:
            bid_ass.max_bid = max_bid_amount
            bid_ass.save()
            messages.success(request, "Bid Assistant updated successfully.")
        else:
            messages.error(request, "Bid Assistant not found.")
    return redirect("assistant_info")


@login_required(login_url='login')
def bid_assistant_delete(request, auction_id):
    bid_ass = BidAssistant.objects.filter(user=request.user, auction__id=auction_id).first()
    if bid_ass:
        bid_ass.delete()
        messages.success(request, "Bid Assistant deleted successfully.")
    else:
        messages.error(request, "Bid Assistant not found.")
    return redirect("assistant_info")


@login_required(login_url='login')
def get_notification(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    formated_notifications = [
        {
            'message': notification.message,
            'created_at': notification.created_at,
            'is_read': notification.is_read,
            'id': notification.pk,
        }
        for notification in notifications
    ]
    return JsonResponse({'notifications': formated_notifications}, safe=False)


@login_required(login_url='login')
def read_notification(request, id):
    Notification.objects.filter(pk=id).update(is_read=True)
    return JsonResponse({'message': 'Notification marked as read successfully.'}, status=200)


@login_required(login_url='login')
def delete_all_notification(request):
    Notification.objects.filter(user=request.user).delete()
    return JsonResponse({'message': 'Notifications deleted successfully.'}, status=200)
