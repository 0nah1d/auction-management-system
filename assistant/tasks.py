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

    for assistant in assistants:
        auction = assistant.auction
        current_highest_bid = auction.get_highest_bid() or 0
        max_bid = assistant.max_bid

        if auction.get_highest_bid_user() == assistant.user or max_bid <= current_highest_bid:
            continue

        next_bid = dynamic_bid_logic(current_highest_bid, max_bid, auction.expire_date)

        if next_bid > current_highest_bid:
            Bids.objects.create(user=assistant.user, auction=auction, bid=next_bid)
            assistant.last_bid_time = current_time
            assistant.save()

            message = f"The assistant has placed a bid of {next_bid}৳ on {auction.title}."
            Notification.objects.create(user=assistant.user, message=message)

            async_to_sync(get_channel_layer().group_send)(
                f"auction_{assistant.user.id}_notifications",
                {"type": "send_notification", "message": message}
            )
