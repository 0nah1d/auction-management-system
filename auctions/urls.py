from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views
from .views import edit_profile_picture

urlpatterns = [
    path("", views.index, name="index"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("create", views.create, name="create"),
    path("auctions", views.auction_list, name="auctionList"),
    path("auction/<int:list_id>", views.auction_details, name="auctionDetails"),
    path("delete/<int:auction_id>", views.delete_auction, name="deleteAuction"),
    path("edit/<int:auction_id>", views.update, name="update"),
    path('auctions/remove_image/', views.remove_image, name='remove_image'),

    path("user/bid", views.user_bid, name="userBids"),
    path("user/profile", views.user_profile, name="userProfile"),
    path('user/profile/edit/', views.edit_profile, name='edit_profile'),
    path('edit-profile-picture/', edit_profile_picture, name='edit_profile_picture'),
    path("user/win/bids", views.user_win_bids, name="userWinBids"),
    path('user/auction', views.myauction, name="myAuction"),
    path("contact", views.contact, name="contact"),
    path("dashboard", views.dashboard, name="userDashboard"),
    path("payment_information/", views.payment_information, name="paymentInformation"),
    path("bidlist", views.bid, name="bid"),
    path("win_ner", views.win_ner, name="win_ner"),
    path("comment", views.comment, name="comment"),

    path('shipping/to/', views.shipping_to, name='shipping_to'),
    path('shipping/from/', views.shipping_from, name='shipping_from'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
