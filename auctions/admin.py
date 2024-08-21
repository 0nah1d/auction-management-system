from django.contrib import admin
from .models import *


# Register your models here.
class AuctionCategoryAdmin(admin.TabularInline):
    model = AuctionCategory
    extra = 1


class auction(admin.ModelAdmin):
    inlines = [
        AuctionCategoryAdmin,
    ]
    list_display = (
    "id", "user", "active_bool", "title", "display_categories", "short_desc", "starting_bid", "buy_now_price")

    def display_categories(self, obj):
        return ", ".join([category.title for category in obj.categories.all()])

    display_categories.short_description = "Categories"


class watchl(admin.ModelAdmin):
    list_display = ("id", "watch_list", "user")


class bds(admin.ModelAdmin):
    list_display = ("id", "user", "listingid", "bid")


class comme(admin.ModelAdmin):
    list_display = ("id", "user", "comment", "listingid")


class win(admin.ModelAdmin):
    list_display = ("id", "user", "bid_win_list")


class user(admin.ModelAdmin):
    list_display = ("id", "username", "email")


class category(admin.ModelAdmin):
    list_display = ("id", "title")


admin.site.register(AuctionList, auction)
admin.site.register(Bids, bds)
admin.site.register(Comments, comme)
admin.site.register(Watchlist, watchl)
admin.site.register(Winner, win)
admin.site.register(User, user)
admin.site.register(Category, category)
admin.site.register(AuctionImage)


