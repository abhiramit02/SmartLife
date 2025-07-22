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

# Try importing sounddevice (for local use only)
try:
    import sounddevice as sd
    import scipy.io.wavfile as wav
    import torchaudio
    SOUND_AVAILABLE = True
except (OSError, Exception):
    SOUND_AVAILABLE = False

SAMPLE_RATE = 16000
DURATION = 5
DEVICE = "cpu"  # Use CPU for Streamlit Cloud

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
    import torchaudio
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

def speak_streamlit(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name
        tts.save(temp_path)
        audio_bytes = open(temp_path, "rb").read()
    os.remove(temp_path)
    return io.BytesIO(audio_bytes)

def main():
    st.title("🗣️ Voice Assistant")

    models = load_models()
    whisper_processor, whisper_model = models["whisper"]
    blender_tokenizer, blender_model = models["blender"]

    st.markdown("### 🔧 Input Methods")
    uploaded_audio = None

    if SOUND_AVAILABLE:
        st.success("🎙️ Microphone supported on local machine.")
        if st.button("🎤 Record Voice"):
            try:
                record_audio()
                uploaded_audio = "user_input.wav"
                st.info("✅ Audio recorded. Ready for transcription.")
            except Exception as e:
                st.error(f"❌ Error during recording: {e}")
    else:
        st.warning("⚠️ Microphone not supported on Streamlit Cloud.")
        uploaded_audio_file = st.file_uploader("📤 Upload a `.wav` file", type=["wav"])
        if uploaded_audio_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(uploaded_audio_file.read())
                uploaded_audio = temp_audio.name
            st.info("✅ Audio uploaded.")

    text_input = st.text_input("✍️ Or type your command here:")

    if uploaded_audio:
        try:
            command = speech_to_text(uploaded_audio, whisper_processor, whisper_model)
            st.markdown(f"📝 **Transcription:** `{command}`")

            reply = get_response_from_model(command, blender_tokenizer, blender_model)
            st.markdown(f"💬 **Response:** `{reply}`")

            audio_data = speak_streamlit(reply)
            st.audio(audio_data, format="audio/mp3")

        except Exception as e:
            st.error(f"❌ Error processing audio: {e}")

    elif text_input.strip():
        try:
            command = text_input.strip()
            st.markdown(f"📝 **Command:** `{command}`")

            reply = get_response_from_model(command, blender_tokenizer, blender_model)
            st.markdown(f"💬 **Response:** `{reply}`")

            audio_data = speak_streamlit(reply)
            st.audio(audio_data, format="audio/mp3")

        except Exception as e:
            st.error(f"❌ Error: {e}")
    else:
        st.info("🎧 Please upload audio or type your command.")

if __name__ == "__main__":
    main()
