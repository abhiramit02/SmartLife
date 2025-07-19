import sounddevice as sd
import scipy.io.wavfile as wav
import torch
from transformers import (
    AutoProcessor, AutoModelForSpeechSeq2Seq,
    BlenderbotTokenizer, BlenderbotForConditionalGeneration
)
from gtts import gTTS
import os
import torchaudio
import io
import streamlit as st
import tempfile

SAMPLE_RATE = 16000
DURATION = 5

# ✅ Use CPU for Streamlit compatibility
DEVICE = "cpu"

# ✅ Load models only once and reuse them across Streamlit reruns
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
    recording = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    wav.write(filename, SAMPLE_RATE, recording)

def speech_to_text(audio_path, processor, model):
    speech_array, _ = torchaudio.load(audio_path)
    inputs = processor(speech_array.squeeze(), sampling_rate=SAMPLE_RATE, return_tensors="pt").to(DEVICE)

    predicted_ids = model.generate(
        **inputs,
        max_new_tokens=128,
        num_beams=3,
        early_stopping=True
    )
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return transcription.strip()

def get_response_from_model(user_input, tokenizer, model):
    inputs = tokenizer(user_input, return_tensors="pt").to(DEVICE)

    outputs = model.generate(
        **inputs,
        max_new_tokens=80,
        num_beams=3,
        early_stopping=True
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.strip()

def speak_streamlit(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name
        tts.save(temp_path)
        audio_bytes = open(temp_path, "rb").read()
    os.remove(temp_path)
    return io.BytesIO(audio_bytes)

# 🔁 Main voice assistant function
def voice_assistant():
    try:
        models = load_models()
        whisper_processor, whisper_model = models["whisper"]
        blender_tokenizer, blender_model = models["blender"]

        record_audio()
        command = speech_to_text("user_input.wav", whisper_processor, whisper_model)

        if not command.strip():
            return None, None, "Couldn't understand your voice. Please try again."

        reply = get_response_from_model(command, blender_tokenizer, blender_model)
        audio_data = speak_streamlit(reply)
        return audio_data, command, reply

    except torch.cuda.OutOfMemoryError:
        return None, None, "❌ CUDA Out of Memory. Try restarting your app or switch to CPU execution."

# ✅ Call this from your Streamlit app
def main():
    return voice_assistant()
