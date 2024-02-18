# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from audojifactory.models import AudioFile, AudioSegment
from audojifactory.serializers import AudioSegmentSerializer

class AudioSegmentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        user_id = text_data_json.get('user_id')
        title = text_data_json.get('title')
        transcription = text_data_json.get('transcription')
        category = text_data_json.get('category')
        
        segments = await self.get_audio_segments(user_id, title, transcription, category)
        await self.send(text_data=json.dumps({
            'segments': segments
        }))

    @database_sync_to_async
    def get_audio_segments(self, user_id, title, transcription, category):
        audio_files_query = AudioFile.objects.all()

        if user_id:
            audio_files_query = audio_files_query.filter(owner=user_id)
        if title:
            audio_files_query = audio_files_query.filter(title__icontains=title)

        segments_query = AudioSegment.objects.filter(audio_file__in=audio_files_query)
        
        if transcription:
            segments_query = segments_query.filter(transcription__icontains=transcription)
        if category:
            segments_query = segments_query.filter(category__icontains=category)

        serializer = AudioSegmentSerializer(segments_query, many=True)
        return serializer.data
