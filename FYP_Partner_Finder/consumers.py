import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import AppUser, Conversation, Message
from .serializer import MessageSerializer

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_name = f"chat_{self.conversation_id}"

        # Add this connection to the room
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Remove user from room
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        sender_id = data["sender_id"]
        receiver_id = data["receiver_id"]
        content = data["content"]

        # Save message to DB
        message = await self.save_message(sender_id, receiver_id, content)

        # Send to the other user only
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_message",
                "message": MessageSerializer(message).data
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket client
        await self.send(text_data=json.dumps(event["message"]))

    # <<<<< THIS IS CRITICAL >>>>>
    @sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        # Fetch sender and receiver objects
        sender = AppUser.objects.get(id=sender_id)
        receiver = AppUser.objects.get(id=receiver_id)

        # Try to find an existing conversation (either order)
        conversation = (
                Conversation.objects.filter(user1=sender, user2=receiver).first()
                or Conversation.objects.filter(user1=receiver, user2=sender).first()
        )

        # If no conversation exists, create it
        if not conversation:
            conversation = Conversation.objects.create(
                user1=sender,
                user2=receiver
            )
            # Update room name dynamically
            self.conversation_id = conversation.id
            self.room_name = f"chat_{conversation.id}"

        # Create and return the message, including receiver
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            receiver=receiver,  # <--- IMPORTANT: save the receiver now
            content=content
        )

        return message