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

# Try importing sounddevice only if local
try:
    import sounddevice as sd
    import scipy.io.wavfile as wav
    import torchaudio
    SOUND_AVAILABLE = True
except OSError:
    SOUND_AVAILABLE = False
except Exception:
    SOUND_AVAILABLE = False

SAMPLE_RATE = 16000
DURATION = 5
DEVICE = "cpu"  # Streamlit Cloud supports only CPU

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
    models = load_models()
    whisper_processor, whisper_model = models["whisper"]
    blender_tokenizer, blender_model = models["blender"]

    try:
        if SOUND_AVAILABLE:
            record_audio()
            command = speech_to_text("user_input.wav", whisper_processor, whisper_model)
        else:
            command = st.text_input("🎤 Microphone not supported on cloud. Type your command:")

        if not command.strip():
            return None, None, "⚠️ No input detected."

        reply = get_response_from_model(command, blender_tokenizer, blender_model)
        audio_data = speak_streamlit(reply)
        return audio_data, command, reply

    except Exception as e:
        return None, None, f"❌ Error occurred: {str(e)}"

# ✅ Entry point for Streamlit
def main():
    models = load_models()
    whisper_processor, whisper_model = models["whisper"]
    blender_tokenizer, blender_model = models["blender"]

    st.title("🗣️ Voice Assistant")

    uploaded_audio = None

    if SOUND_AVAILABLE:
        st.success("🎙️ Microphone support available on local machine.")
        if st.button("Record and Respond"):
            record_audio()
            uploaded_audio = "user_input.wav"
    else:
        st.warning("⚠️ Microphone not supported on cloud. Please upload a WAV file.")
        uploaded_audio_file = st.file_uploader("Upload your .wav file", type=["wav"])
        if uploaded_audio_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(uploaded_audio_file.read())
                uploaded_audio = temp_audio.name

    if uploaded_audio:
        try:
            command = speech_to_text(uploaded_audio, whisper_processor, whisper_model)
            st.markdown(f"📝 Transcription: `{command}`")

            reply = get_response_from_model(command, blender_tokenizer, blender_model)
            st.markdown(f"💬 Response: `{reply}`")

            audio_data = speak_streamlit(reply)
            st.audio(audio_data, format="audio/mp3")
        except Exception as e:
            st.error(f"❌ Error occurred: {e}")
