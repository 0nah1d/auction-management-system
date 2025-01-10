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
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid HTTP method'}, status=405)

    try:
        data = json.loads(request.body)
        max_bid_amount = data.get('max_bid')

        if max_bid_amount is None or not isinstance(max_bid_amount, (int, float)) or max_bid_amount <= 0:
            return JsonResponse({'error': 'Invalid max_bid value. It must be a positive number.'}, status=400)

        auction = get_object_or_404(AuctionList, pk=auction_id)

        if max_bid_amount < auction.get_highest_bid():
            return JsonResponse({'error': 'The amount must be heigher then current bid number.'})

        assAuction = BidAssistant.objects.create(
            user=request.user,
            auction=auction,
            max_bid=max_bid_amount,
        )
        return JsonResponse({'message': 'Bid Assistant set successfully.'})

    except Http404:
        return JsonResponse({'error': 'Auction not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)


@login_required(login_url='login')
def bid_assistant(request):
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
