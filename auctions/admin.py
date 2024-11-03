from django.contrib import admin
from .models import *



admin.site.register(User)
admin.site.register(Address)
admin.site.register(AuctionList)
admin.site.register(AuctionImage)
admin.site.register(Category)
admin.site.register(AuctionCategory)
admin.site.register(Bids)
admin.site.register(Comments)
admin.site.register(Winner)




