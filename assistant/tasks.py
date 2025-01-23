from celery import shared_task
from assistant.utils import dynamic_bid_logic
from auctions.models import Bids, AuctionList, Winner
from assistant.models import BidAssistant, Notification
from django.utils.timezone import now
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


@shared_task
def intelligent_auto_bid_task():
    current_time = now()

    # Fetch assistants with their auctions and related data
    assistants = BidAssistant.objects.select_related('auction', 'user').filter(
        auction__expire_date__gt=current_time,
        auction__active_bool=True
    )

    for assistant in assistants:
        auction = assistant.auction
        current_highest_bid = auction.get_highest_bid() or 0
        max_bid = assistant.max_bid

        # Skip if the assistant's user is already the highest bidder or if max_bid is too low
        if auction.get_highest_bid_user() == assistant.user or max_bid <= current_highest_bid:
            continue

        # Determine the next bid
        next_bid = dynamic_bid_logic(current_highest_bid, max_bid, auction.expire_date, auction.created_at)

        if next_bid > current_highest_bid:
            # Place the bid
            Bids.objects.create(user=assistant.user, auction=auction, bid=next_bid)
            assistant.last_bid_time = current_time
            assistant.save()

            # Create and send a notification
            message = f"The assistant has placed a bid of {next_bid}৳ on {auction.title}."
            Notification.objects.create(user=assistant.user, message=message)

            async_to_sync(get_channel_layer().group_send)(
                f"auction_{assistant.user.id}_notifications",
                {"type": "send_notification", "message": message}
            )


@shared_task
def winner_notify_task():
    current_time = now()

    expired_auctions = AuctionList.objects.filter(expire_date__lte=current_time, active_bool=True).prefetch_related(
        'bids')

    for auction in expired_auctions:
        # auction.active_bool = False
        # auction.save()

        highest_bid = auction.bids.order_by('-bid').first()
        if highest_bid:
            winner_user = highest_bid.user

            if not Winner.objects.filter(bid_win_list=auction).exists():
                Winner.objects.create(bid_win_list=auction, user=winner_user)

                message = f"Congratulations {winner_user.username}! You have won the auction '{auction.title}'."
                Notification.objects.create(user=winner_user, message=message)
                async_to_sync(get_channel_layer().group_send)(
                    f"auction_{winner_user.id}_notifications",
                    {"type": "send_notification", "message": message}
                )
