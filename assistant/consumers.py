from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json

import logging

logger = logging.getLogger(__name__)


class AuctionNotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f"auction_{self.user_id}_notifications"

        self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def send_notification(self, event):
        message = event['message']
        logger.info(f"Notification: {message}")

        self.send(text_data=json.dumps({
            'message': message
        }))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
