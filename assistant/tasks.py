from celery import shared_task
from django.utils import timezone
from auctions.models import AuctionList, Bids, BidAssistant
import math


@shared_task
def auto_bid_task():
    current_time = timezone.now()

    # Retrieve active BidAssistants for auctions that haven’t expired
    assistants = BidAssistant.objects.select_related('auction').filter(
        auction__expire_date__gt=current_time,
        auction__active_bool=True
    )

    for assistant in assistants:
        auction = assistant.auction
        time_remaining = (auction.expire_date - current_time).total_seconds()

        current_highest_bid = auction.get_highest_bid()
        max_bid = assistant.max_bid
        bid_gap = max_bid - current_highest_bid

        # Determine a dynamic increment based on bidding conditions
        if bid_gap <= 10:
            # If close to max bid, use a smaller increment
            increment = 1
        elif time_remaining <= 300:
            # Larger increment as auction nears end to deter competitors
            increment = min(bid_gap, 20)
        elif bid_gap < 50:
            # Moderate increment if the gap is small
            increment = min(bid_gap, 5)
        else:
            # If there is a large gap, use a higher increment
            increment = min(bid_gap, 10)

        next_bid = current_highest_bid + increment

        # Ensure next bid does not exceed max bid
        if next_bid <= max_bid:
            # Place the bid
            Bids.objects.create(user=assistant.user, auction=auction, bid=next_bid)

            # Update last bid time
            assistant.last_bid_time = current_time
            assistant.save()

            print(f"Dynamic bid of {next_bid} placed for {assistant.user.username} on {auction.title}")


@shared_task
def notify_user_about_new_bid(auction_id, bid_amount, user_id):
    auction = AuctionList.objects.get(id=auction_id)
    message = f"New bid of {bid_amount} placed on {auction.title}. Auction ends soon!"

    # Publish the notification to the auction channel
    channel = f"auction_{auction.id}_notifications"
    publish_notification(channel, message)
