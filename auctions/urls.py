from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views
from .views import edit_profile_picture
from .payment import initiate_payment, payment_status

urlpatterns = [
    path("", views.index, name="index"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("create", views.create, name="create"),
    path("auctions", views.auction_list, name="auctionList"),
    path("auction/<int:bidid>", views.auction_details, name="auctionDetails"),
    path("delete/<int:auction_id>", views.delete_auction, name="deleteAuction"),
    path("edit/<int:auction_id>", views.update, name="update"),
    path('auctions/remove_image/', views.remove_image, name='remove_image'),

    path("user/bid", views.user_bid, name="userBids"),
    path("user/profile", views.user_profile, name="userProfile"),
    path('edit-profile-picture/', edit_profile_picture, name='edit_profile_picture'),
    path("user/win/bids", views.user_win_bids, name="userWinBids"),
    path('user/auction', views.myauction, name="myAuction"),
    path("contact", views.contact, name="contact"),
    path("dashboard", views.dashboard, name="userDashboard"),
    path("bidlist", views.bid, name="bid"),
    path("win_ner", views.win_ner, name="win_ner"),

    path('initiate_payment/', initiate_payment, name='paymentPage'),
    path('payment_status/', payment_status, name='payment_status'),
    # path('payment_complete/', )
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
