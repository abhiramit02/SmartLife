import streamlit as st
import asyncio
import queue
import threading
import time
import tempfile
import os
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import numpy as np
import soundfile as sf
from gtts import gTTS
import io

class VoiceRecorder:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.recording = False
        self.audio_frames = []
        
    def audio_frame_callback(self, frame):
        if self.recording:
            self.audio_frames.append(frame.to_ndarray())
        return frame
    
    def start_recording(self):
        self.recording = True
        self.audio_frames = []
        
    def stop_recording(self):
        self.recording = False
        return self.audio_frames
    
    def save_audio(self, frames, sample_rate=16000):
        if not frames:
            return None
            
        # Convert frames to audio data
        audio_data = np.concatenate(frames, axis=0)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            return tmp_file.name

def create_voice_recorder():
    """Create a voice recorder component"""
    
    # Initialize recorder
    if 'voice_recorder' not in st.session_state:
        st.session_state.voice_recorder = VoiceRecorder()
    
    recorder = st.session_state.voice_recorder
    
    # WebRTC configuration
    rtc_configuration = RTCConfiguration({
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })
    
    # Create the WebRTC streamer
    webrtc_ctx = webrtc_streamer(
        key="voice-recorder",
        mode=WebRtcMode.SENDONLY,
        audio_frame_callback=recorder.audio_frame_callback,
        rtc_configuration=rtc_configuration,
        media_stream_constraints={
            "video": False,
            "audio": {
                "sampleRate": 16000,
                "channelCount": 1,
                "echoCancellation": True,
                "noiseSuppression": True,
            }
        },
        async_processing=True,
    )
    
    # Recording controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎙️ Start Recording", type="primary"):
            if webrtc_ctx.state.playing:
                recorder.start_recording()
                st.success("🎤 Recording started! Speak now...")
            else:
                st.warning("⚠️ Please allow microphone access first")
    
    with col2:
        if st.button("⏹️ Stop Recording"):
            if recorder.recording:
                frames = recorder.stop_recording()
                if frames:
                    # Save audio to temporary file
                    audio_file = recorder.save_audio(frames)
                    st.session_state.recorded_audio_file = audio_file
                    st.success(f"✅ Recording saved! ({len(frames)} frames)")
                else:
                    st.warning("⚠️ No audio recorded")
            else:
                st.info("ℹ️ No recording in progress")
    
    with col3:
        if st.button("🔄 Reset"):
            recorder.recording = False
            recorder.audio_frames = []
            if 'recorded_audio_file' in st.session_state:
                del st.session_state.recorded_audio_file
            st.success("🔄 Reset complete")
    
    # Show recording status
    if recorder.recording:
        st.markdown("🔴 **Recording in progress...**")
        st.markdown("💡 *Speak clearly into your microphone*")
    
    # Show recorded audio if available
    if 'recorded_audio_file' in st.session_state and st.session_state.recorded_audio_file:
        st.markdown("---")
        st.subheader("🎵 Recorded Audio")
        
        # Read and display the recorded audio
        try:
            with open(st.session_state.recorded_audio_file, 'rb') as f:
                audio_bytes = f.read()
            
            st.audio(audio_bytes, format='audio/wav')
            
            col_download, col_delete = st.columns(2)
            with col_download:
                st.download_button(
                    label="📥 Download Recording",
                    data=audio_bytes,
                    file_name="voice_recording.wav",
                    mime="audio/wav"
                )
            
            with col_delete:
                if st.button("🗑️ Delete Recording"):
                    try:
                        os.unlink(st.session_state.recorded_audio_file)
                        del st.session_state.recorded_audio_file
                        st.success("🗑️ Recording deleted")
                        st.rerun()
                    except:
                        st.error("❌ Error deleting file")
                        
        except Exception as e:
            st.error(f"❌ Error reading audio file: {str(e)}")
    
    return webrtc_ctx

def text_to_speech(text, lang='en'):
    """Convert text to speech and return audio bytes"""
    try:
        tts = gTTS(text=text, lang=lang)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tts.save(tmp_file.name)
            
            # Read the file
            with open(tmp_file.name, 'rb') as f:
                audio_bytes = f.read()
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return io.BytesIO(audio_bytes)
    except Exception as e:
        st.error(f"❌ Text-to-speech error: {str(e)}")
        return None
