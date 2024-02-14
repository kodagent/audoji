import io
import json
import os
import tempfile

import librosa
import openai
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.files.base import ContentFile
from openai import AsyncOpenAI
from pydub import AudioSegment as AudioSegmentCreator

from audojiengine.logging_config import configure_logger
from audojiengine.mg_database import store_data_to_audio_segment_mgdb
from audojifactory.models import AudioSegment as AudioSegmentModel

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
logger = configure_logger(__name__)


class AudioProcessor:
    def __init__(self, audio_file_instance):
        import whisper

        self.audio_file_instance = audio_file_instance
        self.audio_path = audio_file_instance.audio_file.path
        self.model = whisper.load_model(
            "base"
        )  # "base", "medium", "large-v1", "large-v2", "large-v3", "large"
        # self.output_dir = self.create_output_directory()

    def create_output_directory(self):
        # Assuming 'media' is the name of your Django media directory
        media_root = settings.MEDIA_ROOT

        # Generate the output directory name based on the audio file name
        base_name = os.path.splitext(os.path.basename(self.audio_path))[0]

        # Construct the output directory path within the media directory
        output_dir = os.path.join(media_root, "audio_segments", base_name)

        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        return output_dir

    # def analyze_tempo(self, segment_audio):
    #     # Save the segment to a temporary file
    #     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
    #         segment_audio.export(temp_file.name, format="wav")

    #         # Load the temporary file with librosa
    #         y, sr = librosa.load(temp_file.name, sr=None)
    #         tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    #     os.remove(temp_file.name)

    #     return {"tempo": tempo}

    async def transcribe_audio(self):
        return self.model.transcribe(self.audio_path)

    async def analyze_mood_async(self, transcription):
        logger.info("Analysing moods")

        categories = "Affection, Gratitude, Apologies, Excitement, Disinterest, Well-being, Greetings"

        prompt = f"""Here's an example of how I want you to categorize the mood: \n
            Text: 'I feel amazing today!' Response: {{'category': 'Excitement'}}\n\n
            fNow, using the same format, categorize the following text as {categories}, and respond in JSON format: \n
            fText: '{transcription}'\nResponse: 

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
            logger.info(f"This is the response: {processed_response}")
            mood = processed_response.get("mood", None)
            return mood
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    async def process_and_save_segments(self, result):
        logger.info("Processing Started")
        segments_data = []

        for i, segment in enumerate(result["segments"]):
            transcription = segment.get("text", "").strip()
            mood = await self.analyze_mood_async(transcription)

            start = segment["start"]
            end = segment["end"]

            # Create a segment instance and save it to the database
            segment_data = {
                "audio_file": self.audio_file_instance,
                "start_time": start,
                "end_time": end,
                "transcription": transcription,
                "mood": mood,
            }
            audio_segment_instance = AudioSegmentModel(**segment_data)
            await sync_to_async(audio_segment_instance.save)()

            segment_data["audio_file_id"] = self.audio_file_instance.id
            del segment_data["audio_file"]
            await store_data_to_audio_segment_mgdb(segment_data)

            logger.info(
                f"Segment {i} exported and saved: Text: {segment.get('text', '')} | Start - {segment['start']}s, End - {segment['end']}s"
            )

        logger.info("Done Creating Audojis")

    async def run_and_save_segments(self):
        logger.info("Run operation started!")
        transcription_result = await self.transcribe_audio()
        return await self.process_and_save_segments(transcription_result)


class AudioRetrieval:
    def __init__(self, matching_segment_instance):
        self.audio_file_instance = matching_segment_instance
        self.segment_id = matching_segment_instance.id
        self.associated_audio_file = (
            matching_segment_instance.audio_file.audio_file.path
        )
        self.start_time = matching_segment_instance.start_time
        self.end_time = matching_segment_instance.end_time

    def create_audoji(self):
        audio = AudioSegmentCreator.from_file(self.associated_audio_file)
        start_ms, end_ms = float(self.start_time * 1000), float(self.end_time * 1000)
        segment_audio = audio[start_ms:end_ms]

        # Create an in-memory file for the segment
        segment_file = io.BytesIO()
        segment_audio.export(segment_file, format="mp3", bitrate="192k")
        segment_file.seek(0)

        segment_file_name = f"segment_{self.segment_id}.mp3"
        self.audio_file_instance.segment_file.save(
            segment_file_name, ContentFile(segment_file.read()), save=False
        )
        self.audio_file_instance.save()

        segment_info = {
            "id": self.audio_file_instance.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "transcription": self.audio_file_instance.transcription,
            "file_url": self.audio_file_instance.segment_file.url,
        }
        return segment_info


# # Usage
# # audio_path = r"C:\Users\pc\Desktop\audoji\Sam-Smith-Beautiful.mp3"
# audio_path = r"C:\Users\pc\Desktop\audoji\Sam-Smith-Man-I-Am.mp3"
# processor = AudioProcessor(audio_path)
# processor.run()
