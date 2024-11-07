import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from assistant.consumers import AuctionNotificationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'commerce.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/auction/<int:auction_id>/notifications/', AuctionNotificationConsumer.as_asgi()),
        ])
    ),
})
