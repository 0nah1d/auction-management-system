import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class AuctionNotificationConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs']['user_id']
        room_group_name = f"auction_{user_id}_notifications"
        self.room_group_name = room_group_name
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def send_notification(self, event):
        message = event['message']
        self.send(text_data=json.dumps({'message': message}))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
