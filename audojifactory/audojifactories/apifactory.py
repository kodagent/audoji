import io
import json
import os
import re
import tempfile
import shutil

import librosa
import openai
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.files.base import ContentFile
from openai import AsyncOpenAI
from pydub import AudioSegment

from audojiengine.logging_config import configure_logger
from audojifactory.audojifactories.opensourcefactory import AudioRetrieval
from audojifactory.models import AudioSegment as AudioSegmentModel
from audojifactory.serializers import AudioSegmentSerializer

import requests
import tempfile

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
logger = configure_logger(__name__)


class AudioProcessor:
    def __init__(self, audio_file_instance, group_name=None):
        self.group_name = group_name
        self.audio_file_instance = audio_file_instance
        self.audio_path = audio_file_instance.audio_file.url
        self.temp_audio_path = self.download_audio(self.audio_path)

    async def send_segment_to_group(self, segment_data):
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            self.group_name,
            {
                "type": "audio.segment",
                "message": segment_data,
            },
        )

    def download_audio(self, audio_url):
        """Download audio from URL to a temporary file and return the file path."""
        # Download the audio file content from the URL
        response = requests.get(audio_url, stream=True)
        
        # Create a temporary file to hold the audio data
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as self.temp_audio_file:
            shutil.copyfileobj(response.raw, self.temp_audio_file)
            
            # Ensure the file is saved before proceeding
            self.temp_audio_file.flush()
        return self.temp_audio_file.name

    async def cleanup(self):
        """Remove the temporary audio file."""
        if self.temp_audio_path and os.path.exists(self.temp_audio_path):
            os.remove(self.temp_audio_path)

    async def transcribe_audio(self):
        try:
            # Download the audio file content from the URL
            response = requests.get(self.audio_path, stream=True)
            
            # transcript = self.client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="vtt")
            transcript = await openai_client.audio.transcriptions.create(
                file=open(self.temp_audio_path, 'rb'),
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"],
            )
            return transcript
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None

    async def analyze_category_async(self, transcription):
        logger.info("Analysing categories")

        categories = "Affection, Gratitude, Apologies, Excitement, Disinterest, Well-being, Greetings"

        prompt = f"""Here's an example of how I want you to categorize the text: \n
            Text: 'I feel amazing today!' Response: {{'category': 'Excitement'}}\n\n
            Now, using the same format, categorize the following text as {categories}, and respond in JSON format: \n
            Text: '{transcription}'\nResponse: 

            # SAMPLE FORMAT:
            {{'category': 'Excitement'}}"""

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                response_format={"type": "json_object"},
            )
            processed_response = json.loads(response.choices[0].message.content)
            # logger.info(f"Categorization response: {processed_response}")
            category = processed_response.get("category", None)
            return category
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def parse_vtt(self, vtt_content):
        segments = []
        lines = vtt_content.split("\n")
        time_regex = r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})"
        non_sentence_regex = r"^[♪♫]+$"  # Regex to match lines with only musical notes or similar characters

        for i in range(len(lines)):
            match = re.match(time_regex, lines[i])
            if match:
                start_time, end_time = match.groups()
                text = lines[i + 1]
                # Check if the text line is not just musical notes or similar
                if not re.match(non_sentence_regex, text):
                    segments.append((start_time, end_time, text))
        return segments

    def convert_to_ms(self, time_str):
        """Converts a time string to milliseconds."""
        h, m, s = map(float, time_str.split(":"))
        return int((h * 3600 + m * 60 + s) * 1000)

    async def seconds_to_milliseconds(self, seconds):
        """Converts seconds to milliseconds."""
        return seconds * 1000

    async def process_and_save_segments(self, transcript_result):
        logger.info("Processing Started")
        segments_data = []

        # vtt_content = transcript
        # segments = self.parse_vtt(vtt_content)

        audio = AudioSegment.from_file(open(self.temp_audio_path, 'rb'))

        for i, segment in enumerate(transcript_result.segments):
            start = segment.get("start")
            end = segment.get("end")
            text = segment.get("text", "").strip()
            
            category = await self.analyze_category_async(text)
            
            start_ms = await self.seconds_to_milliseconds(start)
            end_ms = await self.seconds_to_milliseconds(end)
            segment_audio = audio[start_ms:end_ms]
            
            # Create a segment instance and save it to the database
            segment_data = {
                "audio_file": self.audio_file_instance,
                "start_time": start,
                "end_time": end,
                "transcription": text,
                "category": category,
            }
            
            audio_segment_instance = AudioSegmentModel(**segment_data)

            await sync_to_async(audio_segment_instance.save)()

            # ==================== Create Audoji ====================
            create_audoji_sync = sync_to_async(
                AudioRetrieval(audio_segment_instance, start, end).create_audoji
            )
            created_audoji = await create_audoji_sync()

            logger.info(f"Audoji created! {created_audoji}")
            # ==================== Create Audoji ====================

            segment_data["audio_file_id"] = self.audio_file_instance.id

            await self.send_segment_to_group(
                AudioSegmentSerializer(audio_segment_instance).data
            )

            logger.info(
                f"Segment {i} exported and saved: Text: {text} | Start - {start_ms}ms, End - {end_ms}ms"
            )

        logger.info("Done Creating Audojis")

    async def run_and_save_segments(self):
        logger.info("Run operation started!")

        transcription_result = await self.transcribe_audio()
        result = await self.process_and_save_segments(transcription_result)
        await self.cleanup()
        return result


# Usage example
# audio_file_instance = [Your AudioFile instance]
# processor = AudioProcessor(audio_file_instance)
# processor.run_and_save_segments(audio_file_instance)
