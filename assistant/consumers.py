from channels.generic.websocket import WebsocketConsumer
import json


class AuctionNotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f"auction_{self.user_id}_notifications"

        self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self):
        self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    def sent_notification(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
