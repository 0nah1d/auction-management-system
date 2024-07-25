from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("auctions", views.auction_list, name="auctionList"),
    path("auction/<int:bidid>", views.auction_details, name="auctionDetails"),

    path("create", views.create, name="create"),
    path("watchlist/<str:username>", views.watchlistpage, name="watchlistpage"),
    path("added", views.addwatchlist, name="addwatchlist"),
    path("delete", views.deletewatchlist, name="deletewatchlist"),
    path("bidlist", views.bid, name="bid"),
    path("comments", views.allcomments, name="allcomments"),
    path("win_ner", views.win_ner, name="win_ner"),
    path("winnings", views.winnings, name="winnings"),
    path("cat_list", views.cat_list, name="cat_list"),
    path("contact", views.contact, name="contact"),
    path("categories/<str:category_name>", views.cat, name="cat"),
    path("dashboard", views.dashboard, name="userDashboard"),
    path("user/bid", views.userBid, name="userBids"),
    path("user/profile", views.userProfile, name="userProfile"),
    path("user/win/bids", views.userWinBids, name="userWinBids"),
    path('user/auction', views.myauction, name="myAuction"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
