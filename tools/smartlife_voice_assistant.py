import os
import io
import tempfile
import streamlit as st
from gtts import gTTS
import torch
from transformers import (
    AutoProcessor, AutoModelForSpeechSeq2Seq,
    BlenderbotTokenizer, BlenderbotForConditionalGeneration
)

# Microphone support (local only)
try:
    import sounddevice as sd
    import scipy.io.wavfile as wav
    import torchaudio
    SOUND_AVAILABLE = True
except Exception:
    SOUND_AVAILABLE = False

SAMPLE_RATE = 16000
DURATION = 5
DEVICE = "cpu"

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

def record_audio(filename="user_input.wav"):
    st.info("🎤 Recording... Please speak into your mic.")
    recording = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    wav.write(filename, SAMPLE_RATE, recording)
    return filename

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

def run_voice_assistant():
    if not SOUND_AVAILABLE:
        return None, None, "❌ Microphone is not available. Run locally to use voice input."

    models = load_models()
    whisper_processor, whisper_model = models["whisper"]
    blender_tokenizer, blender_model = models["blender"]

    audio_path = record_audio()
    command = speech_to_text(audio_path, whisper_processor, whisper_model)
    reply = get_response_from_model(command, blender_tokenizer, blender_model)
    audio_data = speak_response(reply)
    return audio_data, command, reply
