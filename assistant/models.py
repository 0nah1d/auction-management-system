from django.db import models
from auctions.models import User, AuctionList
from django.utils import timezone


class BidAssistant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE, related_name='bid_assistants')
    max_bid = models.IntegerField()
    last_bid_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - Max Bid: {self.max_bid} on {self.auction.title}"


class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.JSONField()  # This will store the subscription data from the client
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE, related_name='subscriptions')

    def __str__(self):
        return f"Subscription for {self.user.username} on auction {self.auction.title}"
