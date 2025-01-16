from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from auctions.models import AuctionList
from .models import BidAssistant
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.paginator import Paginator
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
def assistant_info(request):
    user = request.user
    profile_picture_url = None
    if hasattr(user, 'profile_picture') and user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    # Pagination
    # paginator = Paginator(payments, 5)
    # page_number = request.GET.get("page")
    # page_obj = paginator.get_page(page_number)
    # total_payment = paginator.count

    return render(request, "assistant_information.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
    })
