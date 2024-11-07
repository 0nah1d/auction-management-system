from django.shortcuts import render


@login_required(login_url='login')
def bid_assistant(request):
    auction_id = request.GET.get('auction_id')
    print(auction_id)
