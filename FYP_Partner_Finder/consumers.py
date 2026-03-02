import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import AppUser, Conversation, Message
from .serializer import MessageListSerializer

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        # Remove user from room if it exists
        if hasattr(self, "room_name"):
            await self.channel_layer.group_discard(
                self.room_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            sender_id = int(data["sender_id"])
            receiver_id = int(data["receiver_id"])
            content = data["content"].strip()

            if not content:
                return

        except (KeyError, ValueError, json.JSONDecodeError):
            # Ignore malformed messages
            return

        # Create a unique room for 1-to-1 chat
        self.room_name = f"chat_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"

        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        message = await self.save_message(sender_id, receiver_id, content)
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_message",
                "message": MessageListSerializer(message).data
            }
        )
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        sender = AppUser.objects.get(id=sender_id)
        receiver = AppUser.objects.get(id=receiver_id)

        # Find existing conversation (either order)
        conversation = (
            Conversation.objects.filter(user1=sender, user2=receiver).first()
            or
            Conversation.objects.filter(user1=receiver, user2=sender).first()
        )

        if not conversation:
            conversation = Conversation.objects.create(
                user1=sender,
                user2=receiver
            )

        return Message.objects.create(
            conversation=conversation,
            sender=sender,
            receiver=receiver,
            content=content
        )