import asyncio
from concurrent.futures import ThreadPoolExecutor

# import openai
from django.conf import settings
from openai import OpenAI


class OpenAIChatEngine:
    def __init__(self, api_key, assistant_id):
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id

    async def upload_file(self, file_path):
        with open(file_path, "rb") as file:
            return self.client.files.create(file=file, purpose="assistants")

    async def delete_file(self, file_id, assistant_id):
        self.client.files.delete(file_id=file_id)
        self.client.beta.assistants.files.delete(
            file_id=file_id, assistant_id=assistant_id
        )

    async def create_assistant(self, name, instructions, model, tools, file_id):
        return self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools,
            file_ids=[file_id],
        )

    async def attach_file_to_assistant(self, assistant_id, file_id):
        self.client.beta.assistants.files.create(assistant_id, file_id=file_id)

    async def create_thread(self):
        thread = self.client.beta.threads.create()
        return thread.id

    async def send_message(self, thread_id, message):
        response = self.client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=message
        )
        return response.id

    async def process_run(self, thread_id, assistant_id):
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        return self.client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run.id
        )

    async def get_messages(self, thread_id):
        return self.client.beta.threads.messages.list(thread_id=thread_id)

    async def process_annotations(self, messages):
        message_content = messages.data[0].content[0].text
        annotations = message_content.annotations
        citations = {}

        # Iterate over the annotations and add footnotes
        for index, annotation in enumerate(annotations):
            # Replace the text with a footnote
            message_content.value = message_content.value.replace(
                annotation.text, f" [{index}]"
            )

            # Gather citations based on annotation attributes
            if file_citation := getattr(annotation, "file_citation", None):
                # cited_file = self.client.files.retrieve(file_citation.file_id)
                # citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
                citations[str(index)] = f"{file_citation.quote}"
            # elif (file_path := getattr(annotation, 'file_path', None)):
            #     cited_file = client.files.retrieve(file_path.file_id)
            #     citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
            #     # Note: File download functionality not implemented above for brevity

        # message_content.value += '\n' + '\n'.join(citations)
        return message_content.value, citations

    async def async_wrapper(func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, func, *args, **kwargs)

    # async def wait_for_run_completion(self, thread_id, run_id, timeout=30, check_interval=2):
    async def wait_for_run_completion(self, run, timeout=30, check_interval=2):
        """Wait for the run to complete with a timeout."""
        elapsed_time = 0
        while elapsed_time < timeout:
            if run.status == "completed":
                return True
            await asyncio.sleep(check_interval)
            elapsed_time += check_interval
        return False

    async def handle_chat(self, thread_id, message):
        message_id = await self.send_message(thread_id, message)
        run = await self.process_run(thread_id, self.assistant_id)
        await self.wait_for_run_completion(run)
        messages = await self.get_messages(thread_id)
        processed_message, citations = await self.process_annotations(messages)
        return processed_message, citations, message_id


# Example usage
# chat_engine = OpenAIChatEngine()
# final_text = chat_engine.handle_chat("Your user's initial message")
