from celery import shared_task
from assistant.utils import dynamic_bid_logic
from auctions.models import Bids
from assistant.models import BidAssistant, Notification
from django.utils.timezone import now
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


@shared_task
def intelligent_auto_bid_task():
    current_time = now()

    assistants = BidAssistant.objects.select_related('auction').filter(
        auction__expire_date__gt=current_time,
        auction__active_bool=True
    )

    if assistants:
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

                message = f"The assistant has placed a bid of {next_bid}৳ on {auction.title}."

                # Create a notification
                Notification.objects.create(user=assistant.user, message=message)

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"auction_{assistant.user.id}_notifications",
                    {
                        "type": "send_notification",
                        "message": message,
                    }
                )

    else:
        print("No active auctions to bid on.")
