from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from tinymce import models as tinymce_models
from .manager import CustomUserManager
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pictures', null=True, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.email


class AuctionList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=64)
    desc = tinymce_models.HTMLField()
    starting_bid = models.IntegerField()
    buy_now_price = models.IntegerField(default=0)
    bid_watch_list = models.IntegerField(default=0)
    expire_date = models.DateTimeField(blank=False, null=True)
    categories = models.ManyToManyField('Category', through='AuctionCategory')
    active_bool = models.BooleanField(default=True)

    def get_images(self):
        return self.images.all()

    def get_highest_bid(self):
        highest_bid = self.bids.order_by('-bid').first()
        return highest_bid.bid if highest_bid else self.starting_bid

    def __str__(self):
        return f"Auction id {self.pk}"


class AuctionImage(models.Model):
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE, related_name='images')
    image_url = models.ImageField(upload_to='auction_image')

    def __str__(self):
        return f"Image for auction id {self.auction.pk}"


class Bids(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE, related_name='bids')
    bid = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} bids on {self.auction.title}"



class Winner(models.Model):
    bid_win_list = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} won {self.bid_win_list.pk}"


class Category(models.Model):
    title = models.CharField(max_length=64)
    slug = models.CharField(max_length=64)

    def __str__(self):
        return self.title

class AuctionCategory(models.Model):
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.auction.pk}  {self.category.title}"
    

class Comments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    listing = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    comment = models.TextField()

    def __str__(self):
        return f"Comment by {self.user.username} on {self.listing.title}"
