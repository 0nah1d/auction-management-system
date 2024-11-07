from django.urls import path
from assistant.consumers import AuctionNotificationConsumer

websocket_urlpatterns = [
    path('ws/auction/<int:auction_id>/notifications/', AuctionNotificationConsumer.as_asgi()),
]
