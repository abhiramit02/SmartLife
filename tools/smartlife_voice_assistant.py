import os
import io
import tempfile
import streamlit as st
from gtts import gTTS
import torch
import torchaudio
from transformers import (
    AutoProcessor, AutoModelForSpeechSeq2Seq,
    BlenderbotTokenizer, BlenderbotForConditionalGeneration
)
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av

DEVICE = "cpu"
SAMPLE_RATE = 16000

@st.cache_resource
def load_models():
    whisper_processor = AutoProcessor.from_pretrained("openai/whisper-tiny.en")
    whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-tiny.en").to(DEVICE)

    blender_tokenizer = BlenderbotTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
    blender_model = BlenderbotForConditionalGeneration.from_pretrained("facebook/blenderbot-400M-distill").to(DEVICE)

    return {
        "whisper": (whisper_processor, whisper_model),
        "blender": (blender_tokenizer, blender_model)
    }

def speech_to_text(audio_path, processor, model):
    speech_array, _ = torchaudio.load(audio_path)
    inputs = processor(speech_array.squeeze(), sampling_rate=SAMPLE_RATE, return_tensors="pt").to(DEVICE)
    predicted_ids = model.generate(**inputs, max_new_tokens=128, num_beams=3, early_stopping=True)
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return transcription.strip()

def get_response_from_model(user_input, tokenizer, model):
    inputs = tokenizer(user_input, return_tensors="pt").to(DEVICE)
    outputs = model.generate(**inputs, max_new_tokens=80, num_beams=3, early_stopping=True)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.strip()

def speak_response(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name
        tts.save(temp_path)
        audio_bytes = open(temp_path, "rb").read()
    os.remove(temp_path)
    return io.BytesIO(audio_bytes)

class AudioRecorder(AudioProcessorBase):
    def __init__(self) -> None:
        self.audio_data = b""

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray().tobytes()
        self.audio_data += pcm
        return frame

# Streamlit UI
st.title("🎙️ Voice Assistant")

ctx = webrtc_streamer(
    key="speech",
    mode="SENDONLY",
    in_audio_enabled=True,
    audio_processor_factory=AudioRecorder,
    media_stream_constraints={"audio": True, "video": False},
)

if ctx.audio_processor and st.button("Process Voice Input"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(ctx.audio_processor.audio_data)
        audio_path = f.name

    models = load_models()
    whisper_processor, whisper_model = models["whisper"]
    blender_tokenizer, blender_model = models["blender"]

    try:
        command = speech_to_text(audio_path, whisper_processor, whisper_model)
        st.success(f"🗣️ You said: {command}")
        reply = get_response_from_model(command, blender_tokenizer, blender_model)
        st.info(f"🤖 Assistant: {reply}")

        audio_response = speak_response(reply)
        st.audio(audio_response, format="audio/mp3")

    except Exception as e:
        st.error(f"❌ Error: {e}")
