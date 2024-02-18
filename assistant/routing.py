from django.urls import path

from assistant.consumers import ChatConsumer
from assistant.audojiconsumers import AudioSegmentConsumer

websocket_urlpatterns = [
    path("ws/chat/", ChatConsumer.as_asgi()),
    path('ws/audiosegments/', AudioSegmentConsumer.as_asgi()),
]
