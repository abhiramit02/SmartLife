import sounddevice as sd
import scipy.io.wavfile as wav
import torch
from transformers import (
    AutoProcessor, AutoModelForSpeechSeq2Seq,
    BlenderbotTokenizer, BlenderbotForConditionalGeneration
)
from TTS.api import TTS
import os
import torchaudio
import io
import streamlit as st
import tempfile

SAMPLE_RATE = 16000
DURATION = 5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ✅ Load models only once and reuse them across Streamlit reruns
@st.cache_resource
def load_models():
    whisper_processor = AutoProcessor.from_pretrained("openai/whisper-tiny.en")
    whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-tiny.en").to("cpu")

    blender_tokenizer = BlenderbotTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
    blender_model = BlenderbotForConditionalGeneration.from_pretrained("facebook/blenderbot-400M-distill").to("cpu")

    try:
        tts = TTS(model_name="tts_models/en/ljspeech/glow-tts", progress_bar=False, gpu=torch.cuda.is_available())
    except:
        tts = TTS(model_name="tts_models/en/ljspeech/glow-tts", progress_bar=False, gpu=False)

    return {
        "whisper": (whisper_processor, whisper_model),
        "blender": (blender_tokenizer, blender_model),
        "tts": tts
    }

def record_audio(filename="user_input.wav"):
    recording = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    wav.write(filename, SAMPLE_RATE, recording)

def speech_to_text(audio_path, processor, model):
    speech_array, _ = torchaudio.load(audio_path)
    inputs = processor(speech_array.squeeze(), sampling_rate=SAMPLE_RATE, return_tensors="pt").to("cpu")

    predicted_ids = model.generate(
        **inputs,
        max_new_tokens=128,
        num_beams=3,
        early_stopping=True
    )
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return transcription.strip()

def get_response_from_model(user_input, tokenizer, model):
    inputs = tokenizer(user_input, return_tensors="pt").to("cpu")

    outputs = model.generate(
        **inputs,
        max_new_tokens=80,
        num_beams=3,
        early_stopping=True
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.strip()

def speak_streamlit(text, tts_model):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_path = temp_audio.name
    tts_model.tts_to_file(text=text, file_path=temp_path)
    audio_bytes = open(temp_path, "rb").read()
    os.remove(temp_path)  # Clean up after playing
    return io.BytesIO(audio_bytes)

# 🔁 Main voice assistant function
def voice_assistant():
    try:
        models = load_models()
        whisper_processor, whisper_model = models["whisper"]
        blender_tokenizer, blender_model = models["blender"]
        tts_model = models["tts"]

        record_audio()
        command = speech_to_text("user_input.wav", whisper_processor, whisper_model)

        if not command.strip():
            return None, None, "Couldn't understand your voice. Please try again."

        reply = get_response_from_model(command, blender_tokenizer, blender_model)
        audio_data = speak_streamlit(reply, tts_model)
        return audio_data, command, reply

    except torch.cuda.OutOfMemoryError:
        return None, None, "❌ CUDA Out of Memory. Try restarting your app or switch to CPU execution."

# ✅ Call this from your Streamlit app: tools/smartlife_voice_assistant.py
def main():
    return voice_assistant()
