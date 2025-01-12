from celery import shared_task
from django.utils import timezone

from assistant.utils import dynamic_bid_logic
from auctions.models import AuctionList, Bids
from assistant.models import BidAssistant
from assistant.notifications import publish_notification
from django.utils.timezone import now


@shared_task
def intelligent_auto_bid_task():
    current_time = now()

    # Retrieve active BidAssistants for auctions that haven’t expired
    assistants = BidAssistant.objects.select_related('auction').filter(
        auction__expire_date__gt=current_time,
        auction__active_bool=True
    )

    for assistant in assistants:
        auction = assistant.auction
        current_highest_bid = auction.get_highest_bid()
        max_bid = assistant.max_bid

        # Use dynamic bidding logic to calculate the next bid
        next_bid = dynamic_bid_logic(current_highest_bid, max_bid, auction.expire_date)

        if next_bid and next_bid > current_highest_bid:
            # Place the bid
            Bids.objects.create(user=assistant.user, auction=auction, bid=next_bid)

            # Update last bid time
            assistant.last_bid_time = current_time
            assistant.save()

            print(f"Bid of {next_bid} placed by {assistant.user.username} on {auction.title}")


@shared_task
def notify_user_about_new_bid(auction_id, bid_amount, user_id):
    auction = AuctionList.objects.get(id=auction_id)
    message = f"New bid of {bid_amount} placed on {auction.title}. Auction ends soon!"

    # Publish the notification to the auction channel
    channel = f"auction_{auction.id}_notifications"
    publish_notification(channel, message)
