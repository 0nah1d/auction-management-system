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
    short_desc = models.TextField(default=None, blank=True, null=True)
    desc = tinymce_models.HTMLField()
    starting_bid = models.IntegerField()
    buy_now_price = models.IntegerField(default=0)
    bid_watch_list = models.IntegerField(default=0)
    image_url = models.CharField(max_length=228, default=None, blank=True, null=True)
    expire_date = models.DateTimeField(blank=False, null=True)
    categories = models.ManyToManyField('Category', through='AuctionCategory')
    active_bool = models.BooleanField(default=True)


class Bids(models.Model):
    user = models.CharField(max_length=30)
    listingid = models.IntegerField()
    bid = models.IntegerField()


class Comments(models.Model):
    user = models.CharField(max_length=64)
    comment = models.TextField()
    listingid = models.IntegerField()


class Watchlist(models.Model):
    watch_list = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    user = models.CharField(max_length=64)


class Winner(models.Model):
    bid_win_list = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    user = models.CharField(max_length=64, default=None)


class Category(models.Model):
    title = models.CharField(max_length=64)
    slug = models.CharField(max_length=64)

    def __str__(self):
        return self.title


class AuctionCategory(models.Model):
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
