from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from auctions.models import AuctionList
from .models import BidAssistant
from django.views.decorators.csrf import csrf_exempt
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
            max_bid=max_bid_amount
        )
        return JsonResponse({'message': 'Bid Assistant set successfully.'})

    except Http404:
        return JsonResponse({'error': 'Auction not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
