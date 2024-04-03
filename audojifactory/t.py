import asyncio
import logging

import requests
import whisper
from asgiref.sync import sync_to_async
from decouple import config
from log_config import configure_logger

logger = configure_logger(__name__)


class AudojiCreator:
    def __init__(self, audio_file_url, group_name, callback_url):
        self.audio_file_url = audio_file_url
        self.group_name = group_name
        self.callback_url = callback_url
        self.model = whisper.load_model(
            "large-v3"
        )  # "base", "medium", "large-v1", "large-v2", "large-v3", "large"

    async def transcribe_audio(self):
        # Run the synchronous transcribe method asynchronously
        result = await sync_to_async(self.model.transcribe)(self.audio_file_url)
        return result

    def send_result_to_callback_url(self, transcription_result):
        # Make an HTTP POST request to the Django app's endpoint with the transcription result
        try:
            data = {
                "audio_file_url": self.audio_file_url,
                "transcription_result": transcription_result,
                "group_name": self.group_name,
            }
            response = requests.post(
                self.callback_url,
                json=data,
            )
            response.raise_for_status()
            logger.info(
                f"Successfully sent transcription result to {self.callback_url}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send transcription result: {e}")


def lambda_handler(event, context):
    # Parse the audio file URL and callback URL from the event
    audio_file_url = event["audio_file_url"]
    group_name = event["group_name"]
    callback_url = event["callback_url"]

    # Create an instance of AudojiCreator
    creator = AudojiCreator(audio_file_url, group_name, callback_url)

    # Transcribe the audio file
    result = asyncio.run(creator.transcribe_audio())

    # Send the transcription result to the callback URL
    creator.send_result_to_callback_url(result["text"])

    return {
        "statusCode": 200,
        "body": "Transcription completed and result sent back successfully",
    }


if __name__ == "__main__":
    import sys

    # Example usage with command-line arguments for testing
    audio_file_url = sys.argv[1] if len(sys.argv) > 1 else config("TEST_AUDIO_FILE_URL")
    group_name = sys.argv[2] if len(sys.argv) > 2 else config("GROUP_NAME")
    callback_url = sys.argv[3] if len(sys.argv) > 3 else config("CALLBACK_URL")

    logger.info(f"This is the audio file url: {audio_file_url}")
    logger.info(f"This is the group name: {group_name}")
    logger.info(f"This is the callback url: {callback_url}")

    lambda_handler(
        {
            "audio_file_url": audio_file_url,
            "group_name": group_name,
            "callback_url": callback_url,
        },
        None,
    )
