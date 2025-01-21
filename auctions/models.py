from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.db import models
from tinymce import models as tinymce_models
from .manager import CustomUserManager
from django.utils.translation import gettext_lazy as _
import random
import string
from django.utils.timezone import now


class User(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pictures', null=True, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    zone = models.CharField(max_length=100, blank=True)
    address = models.TextField(null=True, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=15, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.email


class AuctionList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=2000)
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

    def get_highest_bid_user(self):
        highest_bid = self.bids.order_by('-bid').first()
        if highest_bid:
            return highest_bid.user
        return None

    def get_total_active_bids(self):
        return self.bids.count()

    def __str__(self):
        return f"{self.title}"


class ShippingAddress(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
        ('IN_TRANSIT', 'In Transit'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    auction = models.ForeignKey(AuctionList, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='shipping_addresses')
    recipient_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zone = models.CharField(max_length=100, blank=True)
    street_address = models.TextField()
    zip_code = models.CharField(max_length=20)
    additional_instructions = models.TextField(blank=True, null=True)
    tracking_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    estimated_delivery_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_tracking_number():
        prefix = "TRK"
        date_part = now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        return f"{prefix}-{date_part}-{random_part}"

    def __str__(self):
        return f"Shipping for {self.user.username} ({self.city}, {self.province}) - {self.get_status_display()}"


class AuctionImage(models.Model):
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE, related_name='images')
    image_url = models.ImageField(upload_to='auction_image')

    def __str__(self):
        return f"{self.auction.title}"


class Bids(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE, related_name='bids')
    bid = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} bids on {self.auction.title}"


class Winner(models.Model):
    bid_win_list = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} won {self.bid_win_list.title}"


class Category(models.Model):
    title = models.CharField(max_length=64)
    slug = models.CharField(max_length=64)

    def __str__(self):
        return self.title


class AuctionCategory(models.Model):
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.category.title}"


class Comments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.IntegerField(
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.listing.title}"


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auction = models.ForeignKey(AuctionList, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.user.username} - {self.auction.title}"
