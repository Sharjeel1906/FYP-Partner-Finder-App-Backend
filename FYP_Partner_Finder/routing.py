from django.urls import re_path
from .consumers import ChatConsumer  # Import your WebSocket consumer

websocket_urlpatterns = [
    re_path(r"ws/chat/$", ChatConsumer.as_asgi()),
]