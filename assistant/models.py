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
