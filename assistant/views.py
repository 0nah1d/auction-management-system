from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.core import serializers
from auctions.models import AuctionList

@login_required(login_url='login')
def bid_assistant(request, auction_id):
    try:
        auction = get_object_or_404(AuctionList, pk=auction_id)
        serialized_auction = serializers.serialize('json', [auction])
        return JsonResponse({'auction_id': auction_id, 'auction': serialized_auction})
    except Http404:
        return JsonResponse({'error': 'Auction not found'}, status=404)
