import whisperx
import gc
from audojiengine.logging_config import configure_logger
from audojiengine.configs.base_config import openai_client as client

logger = configure_logger(__name__)

audio_file = "https://audojistore.s3.amazonaws.com/media/audio_files/Banky_W_-_Mercy_HIPHOPNAIJA.COM__32YKcVT.mp3"

device = "cuda"
batch_size = 16 # reduce if low on GPU mem
compute_type = "float16" # change to "int8" if low on GPU mem (may reduce accuracy)

class AudioProcessor:
    def __init__(self, audio_file_instance, group_name=None):
        self.group_name = group_name
        self.audio_file_instance = audio_file_instance
        self.audio_path = audio_file_instance.audio_file.url
        self.model = whisperx.load_model("large-v3", device, compute_type=compute_type)
        self.final_list = []

    async def send_segment_to_group(self, segment_data):
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            self.group_name,
            {
                "type": "audio.segment",
                "message": segment_data,
            },
        )

    async def transcribe_audio(self):
        audio = whisperx.load_audio(self.audio_path)
        result = model.transcribe(audio, batch_size=batch_size)

        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
        final_result = result["segments"]
        return final_result

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
            logger.info(f"This is the response: {processed_response}")
            category = processed_response.get("category", None)
            return category
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    async def process_and_save_segments(self, final_list):
        logger.info("Processing Started")
        segments_data = []
        segment_counter = 0

        for i, sentence_segment in enumerate(final_list):
            # Initialize a variable to hold the adjusted start_ms for the next segment
            next_start_ms = None
            next_start_ms_adjustment = 0.0

            for index, segment in enumerate(sentence_segment):
                transcription = segment.get("text", "").strip()
                category = await self.analyze_category_async(transcription)
                
                start_ms = seconds_to_milliseconds(segment["start"] + next_start_ms_adjustment)
                end_ms = seconds_to_milliseconds(segment["end"])

                # Adjust end_ms and plan adjustment for next segment's start_ms based on the score
                if segment["last_word_score"] < 0.35:
                    # end_ms += seconds_to_milliseconds(1)
                    # next_start_ms_adjustment = 0.5
                    if index + 1 < len(sentence_segment):
                        next_segment_start_ms = seconds_to_milliseconds(
                            sentence_segment[index + 1]["start"]
                        )
                        half_distance = (next_segment_start_ms - end_ms) / 2
                        end_ms += half_distance
                    else:
                        end_ms += seconds_to_milliseconds(
                            1
                        )  # Or any other logic for last segment
                    next_start_ms_adjustment = 0.5  # Adjusting next start time by 0.5 seconds                elif segment["last_word_score"] < 0.7:
                    end_ms += seconds_to_milliseconds(0.5)
                    next_start_ms_adjustment = 0.2
                else:
                    next_start_ms_adjustment = 0  # No adjustment needed

                # Create a segment instance and save it to the database
                segment_data = {
                    "audio_file": self.audio_file_instance,
                    "start_time": segment["start"],
                    "end_time": segment["end"],
                    "transcription": transcription,
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
                    f"Segment {i} exported and saved: Text: {segment.get('text', '')} | Start - {segment['start']}s, End - {segment['end']}s"
                )

                segment_counter += 1
                
        logger.info("Done Creating Audojis")