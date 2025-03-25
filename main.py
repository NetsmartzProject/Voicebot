import streamlit as st
import asyncio
import subprocess
import requests
import time
from dotenv import load_dotenv
import os

from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)


# Load environment variables
load_dotenv()


class LanguageModelProcessor:
    def __init__(self):
        self.llm = ChatGroq(temperature=0, model_name="gemma2-9b-it", groq_api_key=os.getenv("GROQ_API_KEY"))
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # Load the system prompt from a file
        with open('prompt.txt', 'r', encoding='utf-8') as file:
            system_prompt = file.read().strip()

        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{text}")
        ])

        self.conversation = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            memory=self.memory
        )

    def process(self, text):
        self.memory.chat_memory.add_user_message(text)

        start_time = time.time()
        response = self.conversation.invoke({"text": text})
        end_time = time.time()

        self.memory.chat_memory.add_ai_message(response['text'])

        elapsed_time = int((end_time - start_time) * 1000)
        st.write(f"LLM ({elapsed_time}ms): {response['text']}")
        return response['text']


class TextToSpeech:
    @staticmethod
    def is_installed(lib_name: str) -> bool:
        try:
            subprocess.run([lib_name, '-version'], check=False, capture_output=True)  # check if installed
            return True
        except FileNotFoundError:
            return False

    def speak(self, text, api_key, model_name):
        if not self.is_installed("ffplay"):
            st.error("ffplay not found, necessary to stream audio.")
            return

        DEEPGRAM_URL = f"https://api.deepgram.com/v1/speak?model={model_name}"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text
        }

        player_command = ["ffplay", "-autoexit", "-", "-nodisp"]
        player_process = subprocess.Popen(
            player_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        start_time = time.time()
        first_byte_time = None

        try:
            with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        if first_byte_time is None:
                            first_byte_time = time.time()
                            ttfb = int((first_byte_time - start_time) * 1000)
                            st.write(f"TTS Time to First Byte (TTFB): {ttfb}ms\n")
                        player_process.stdin.write(chunk)
                        player_process.stdin.flush()

            if player_process.stdin:
                player_process.stdin.close()
            player_process.wait()

        except requests.exceptions.RequestException as e:
            st.error(f"TTS Request Error: {e}")  # more informative error message
        finally:
            if player_process and player_process.poll() is None:
                player_process.kill()  # Ensure process is killed on error

class TranscriptCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.transcript_parts = []

    def add_part(self, part):
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        return ' '.join(self.transcript_parts)


# Initialize Deepgram Client (outside function)
deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
deepgram_config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram_client: DeepgramClient = DeepgramClient(deepgram_api_key, deepgram_config)


async def get_transcript(callback):
    transcription_complete = asyncio.Event()

    try:
        dg_connection = deepgram_client.listen.asynclive.v("1")
        st.write("Listening...")

        transcript_collector = TranscriptCollector()

        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript

            if not result.speech_final:
                transcript_collector.add_part(sentence)
            else:
                transcript_collector.add_part(sentence)
                full_sentence = transcript_collector.get_full_transcript()
                if len(full_sentence.strip()) > 0:
                    full_sentence = full_sentence.strip()
                    st.write(f"Human: {full_sentence}")
                    callback(full_sentence)
                    transcript_collector.reset()
                    transcription_complete.set()

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            endpointing=300,
            smart_format=True,
        )

        # Start and Finish Deepgram Connection together to ensure cleanup
        try:
            await dg_connection.start(options)

            microphone = Microphone(dg_connection.send)
            microphone.start()

            await transcription_complete.wait()

            microphone.finish()
        finally:
            await dg_connection.finish()


    except Exception as e:
        st.error(f"Could not open socket: {e}")
        return


def main():
    st.title("Conversational AI with Speech Transcription")

    # Initialize session state variables
    if 'llm' not in st.session_state:
        st.session_state.llm = LanguageModelProcessor()

    if 'transcription_response' not in st.session_state:
        st.session_state.transcription_response = ""

    # Streamlit button to start conversation
    if st.button("Start Listening"):
        async def conversation_loop():
            def handle_full_sentence(full_sentence):
                st.session_state.transcription_response = full_sentence

            groq_api_key = os.getenv("GROQ_API_KEY")
            deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
            tts_model_name= "aura-hera-en"

            tts = TextToSpeech()

            while True:
                await get_transcript(handle_full_sentence)

                # Check for "goodbye" to exit the loop
                if "goodbye" in st.session_state.transcription_response.lower():
                    st.write("Conversation ended.")
                    break

                llm_response = st.session_state.llm.process(st.session_state.transcription_response)

                tts.speak(llm_response, deepgram_api_key, tts_model_name)

                # Reset transcription_response
                st.session_state.transcription_response = ""

        # Run the async function
        asyncio.run(conversation_loop())


if __name__ == "__main__":
    main()
