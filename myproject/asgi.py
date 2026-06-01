import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

from django.core.asgi import get_asgi_application

# Initialize Django FIRST
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import FYP_Partner_Finder.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            FYP_Partner_Finder.routing.websocket_urlpatterns
        )
    ),
})