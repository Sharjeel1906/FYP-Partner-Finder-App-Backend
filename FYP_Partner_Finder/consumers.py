# Copy this into your Django app (e.g. chat/consumers.py).
# Routing stays the same: ws/chat/<sender_id>/<receiver_id>/
#
# Also ensure presence.py exposes is_user_online(user_id) — see presence_backend.py

import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User

from .models import Conversation, Message
from .presence import mark_user_connected, mark_user_disconnected,is_user_online
from .serializer import MessageListSerializer


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.sender_id = int(self.scope["url_route"]["kwargs"]["sender_id"])
        self.receiver_id = int(self.scope["url_route"]["kwargs"]["receiver_id"])
        self.room_name = (
            f"chat_{min(self.sender_id, self.receiver_id)}_"
            f"{max(self.sender_id, self.receiver_id)}"
        )

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.set_presence(self.sender_id, connected=True)
        await self.accept()

        # Tell everyone in the room this user is online
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "presence_event",
                "user_id": self.sender_id,
                "is_online": True,
            },
        )

        # Tell the connector whether the chat partner is already online
        partner_online = await self.get_user_online(self.receiver_id)
        await self.send(
            text_data=json.dumps(
                {
                    "type": "is_online",
                    "user_id": self.receiver_id,
                    "is_online": partner_online,
                }
            )
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        await self.set_presence(self.sender_id, connected=False)
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "presence_event",
                "user_id": self.sender_id,
                "is_online": False,
            },
        )

    @sync_to_async
    def set_presence(self, user_id, connected):
        if connected:
            mark_user_connected(user_id)
        else:
            mark_user_disconnected(user_id)

    @sync_to_async
    def get_user_online(self, user_id):
        return is_user_online(user_id)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        # Flutter sends: {"typing": true} or {"typing": false}
        if "typing" in data:
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "typing_event",
                    "sender_id": self.sender_id,
                    "typing": bool(data["typing"]),
                },
            )
            return

        msg_type = data.get("type")
        if msg_type == "typing_start":
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "typing_event",
                    "sender_id": self.sender_id,
                    "typing": True,
                },
            )
            return
        if msg_type == "typing_stop":
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "typing_event",
                    "sender_id": self.sender_id,
                    "typing": False,
                },
            )
            return

        try:
            content = data["content"].strip()
            if not content:
                return
        except (KeyError, ValueError, AttributeError):
            return

        message = await self.save_message(
            self.sender_id,
            self.receiver_id,
            content,
        )

        serialized_message = await self.serialize_message(message)

        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_message",
                "message": serialized_message,
            },
        )

    async def typing_event(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing_start" if event["typing"] else "typing_stop",
                    "sender_id": event["sender_id"],
                    "typing": event["typing"],
                }
            )
        )

    async def presence_event(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "is_online",
                    "user_id": event["user_id"],
                    "is_online": event["is_online"],
                }
            )
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @sync_to_async
    def serialize_message(self, message):
        return MessageListSerializer(message).data

    @sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        conversation = (
            Conversation.objects.filter(user1=sender, user2=receiver).first()
            or Conversation.objects.filter(user1=receiver, user2=sender).first()
        )

        if not conversation:
            conversation = Conversation.objects.create(
                user1=min(sender, receiver, key=lambda u: u.id),
                user2=max(sender, receiver, key=lambda u: u.id),
            )

        return Message.objects.create(
            conversation=conversation,
            sender=sender,
            receiver=receiver,
            content=content,
        )
