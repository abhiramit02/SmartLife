import streamlit as st
import queue
import tempfile
import os
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import numpy as np
import soundfile as sf
from gtts import gTTS
import io

# Helper class to collect audio frames
class AudioFrameCollector:
    def __init__(self):
        self.frames = []
        self.recording = False

    def audio_frame_callback(self, frame: av.AudioFrame):
        if self.recording:
            self.frames.append(frame.to_ndarray())
        return frame

    def reset(self):
        self.frames = []

    def save_audio(self, sample_rate=16000):
        if not self.frames:
            return None
        audio_data = np.concatenate(self.frames, axis=0)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sf.write(temp_file.name, audio_data, sample_rate)
        return temp_file.name

def create_voice_recorder():
    if 'audio_collector' not in st.session_state:
        st.session_state.audio_collector = AudioFrameCollector()
    collector = st.session_state.audio_collector

    rtc_configuration = RTCConfiguration({
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

    st.markdown("### 🎤 Voice Recorder")
    st.markdown("**Click 'Start Recording', speak, then click 'Stop Recording'.**")

    # WebRTC streamer
    webrtc_ctx = webrtc_streamer(
        key="voice-recorder",
        mode=WebRtcMode.SENDONLY,
        audio_frame_callback=collector.audio_frame_callback,
        rtc_configuration=rtc_configuration,
        media_stream_constraints={"video": False, "audio": True},
        async_processing=True,
    )

    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'recorded_audio_file' not in st.session_state:
        st.session_state.recorded_audio_file = None

    col1, col2 = st.columns(2)
    with col1:
        if not st.session_state.recording:
            if st.button("🎙️ Start Recording", type="primary"):
                collector.reset()
                collector.recording = True
                st.session_state.recording = True
                st.experimental_rerun()
        else:
            if st.button("⏹️ Stop Recording", type="secondary"):
                collector.recording = False
                st.session_state.recording = False
                # Save audio
                audio_file = collector.save_audio()
                st.session_state.recorded_audio_file = audio_file
                st.success("✅ Recording complete! Your voice has been captured.")
                st.experimental_rerun()
    with col2:
        if st.session_state.recorded_audio_file:
            st.audio(st.session_state.recorded_audio_file, format='audio/wav')
            if st.button("🗑️ Delete Recording"):
                try:
                    os.unlink(st.session_state.recorded_audio_file)
                except:
                    pass
                st.session_state.recorded_audio_file = None
                st.experimental_rerun()

    if st.session_state.recording:
        st.info("🎤 **Recording... Speak now!** Click 'Stop Recording' when you're done.")

    return None

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
            tts.save(temp_path)
            audio_bytes = open(temp_path, "rb").read()
        os.remove(temp_path)
        return io.BytesIO(audio_bytes)
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None
