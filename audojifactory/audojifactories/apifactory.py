import io
import os
import re
import tempfile

import librosa
from django.conf import settings
from django.core.files.base import ContentFile
from openai import OpenAI
from pydub import AudioSegment

from audojiengine.logging_config import configure_logger
from audojifactory.models import AudioSegment as AudioSegmentModel

logger = configure_logger(__name__)


class AudioProcessor:
    def __init__(self, audio_file_instance):
        self.audio_file_instance = audio_file_instance
        self.audio_path = audio_file_instance.file.path
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def extract_metadata(self, segment_audio):
        # Save the segment to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            segment_audio.export(temp_file.name, format="wav")

            # Load the temporary file with librosa
            y, sr = librosa.load(temp_file.name, sr=None)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            # Add more metadata extraction as needed
        
        # Remove the temporary file
        os.remove(temp_file.name)
        
        return {"tempo": tempo}
    
    def transcribe_audio(self):
        try:
            with open(self.audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="vtt")
            return transcript
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None

    def parse_vtt(self, vtt_content):
        segments = []
        lines = vtt_content.split('\n')
        time_regex = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})'
        non_sentence_regex = r'^[♪♫]+$'  # Regex to match lines with only musical notes or similar characters

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
        h, m, s = map(float, time_str.split(':'))
        return int((h * 3600 + m * 60 + s) * 1000)

    def process_and_save_segments(self, transcript, audio_file_instance):
        segments_data = []
        vtt_content = transcript
        segments = self.parse_vtt(vtt_content)

        audio = AudioSegment.from_file(self.audio_path)
        
        for i, (start, end, text) in enumerate(segments):
            start_ms, end_ms = self.convert_to_ms(start), self.convert_to_ms(end)
            segment_audio = audio[start_ms:end_ms]

            # Create an in-memory file for the segment
            segment_file = io.BytesIO()
            segment_audio.export(segment_file, format="mp3", bitrate="192k")
            segment_file.seek(0)

            # Create a segment instance and save it to the database
            audio_segment_instance = AudioSegmentModel(
                audio_file=audio_file_instance,
                start_time=start_ms / 1000,  # Convert ms back to seconds
                end_time=end_ms / 1000,
                transcription=text
            )
            segment_file_name = f"segment_{i}.mp3"
            audio_segment_instance.segment_file.save(segment_file_name, ContentFile(segment_file.read()), save=False)
            audio_segment_instance.save()

            metadata = self.extract_metadata(segment_audio)

            segment_info = {
                "id": audio_segment_instance.id,
                "start_time": end_ms,
                "end_time": start_ms,
                "transcription": text,
                "file_url": audio_segment_instance.segment_file.url,
                "metadata": metadata
            }
            segments_data.append(segment_info)

            logger.info(f"Segment {i} exported and saved: Text: {text} | Start - {start_ms}ms, End - {end_ms}ms")

        return segments_data

    def run_and_save_segments(self, audio_file_instance):
        transcription_result = self.transcribe_audio()
        if transcription_result:
            return self.process_and_save_segments(transcription_result, audio_file_instance)

# Usage example
# audio_file_instance = [Your AudioFile instance]
# processor = AudioProcessor(audio_file_instance)
# processor.run_and_save_segments(audio_file_instance)
