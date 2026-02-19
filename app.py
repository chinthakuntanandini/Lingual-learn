import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS  # Library for Text-to-Speech
from PyPDF2 import PdfReader
import io
import pydub
import os

# --- 1. FFmpeg Configuration ---
# Ensure ffmpeg.exe and ffprobe.exe are in C:\ffmpeg\bin
pydub.AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
pydub.AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"

# --- 2. Page Setup ---
st.set_page_config(page_title="LinguaLearn AI", layout="wide")
st.title("LinguaLearn: AI Inclusive Classroom 🎓")

# Initialize session state for lecture history
if "lecture_history" not in st.session_state:
    st.session_state.lecture_history = ""

# Language mapping for Speech and Translation
# Google Translate codes: English='en', Telugu='te', Urdu='ur'
languages = {
    "English": {"speech": "en-US", "trans": "en"},
    "Telugu": {"speech": "te-IN", "trans": "te"},
    "Urdu": {"speech": "ur-PK", "trans": "ur"}
}

# --- 3. Sidebar Settings ---
st.sidebar.header("Classroom Settings")
fdp_lang = st.sidebar.selectbox("Teacher Language:", list(languages.keys()))
std_lang = st.sidebar.selectbox("Student Language:", list(languages.keys()))

translator = Translator()
recognizer = sr.Recognizer()

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["🎙️ Live Class", "📄 PDF Translate", "🔗 Link/Text"])

# --- TAB 1: Live Class with Audio Output ---
with tab1:
    st.subheader("Live Audio Translation")
    st.info(f"Speaking: {fdp_lang} | Listening: {std_lang}")
    
    # Record voice from the browser
    audio_data = mic_recorder(start_prompt="🎤 Start Class", stop_prompt="🛑 Stop Class", key='live_mic')
    
    if audio_data:
        try:
            # Step A: Convert recorded audio to WAV using FFmpeg
            audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio_data['bytes']))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)
            
            with sr.AudioFile(wav_io) as source:
                audio = recognizer.record(source)
                # Step B: Recognize Teacher's Speech
                original_text = recognizer.recognize_google(audio, language=languages[fdp_lang]["speech"])
                
                # Step C: Translate to Student's Language (e.g., Urdu)
                translated_res = translator.translate(original_text, dest=languages[std_lang]["trans"])
                translated_text = translated_res.text
                
                # Display Text Results
                st.write(f"**Teacher ({fdp_lang}):** {original_text}")
                st.success(f"**Student ({std_lang}):** {translated_text}")
                
                # Step D: Voice Output (Text-to-Speech)
                # This creates an audio player to hear the translation
                tts = gTTS(text=translated_text, lang=languages[std_lang]["trans"])
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')
                
                # Save to history for download
                st.session_state.lecture_history += f"FDP: {original_text}\nStd: {translated_text}\n\n"
                
        except Exception as e:
            st.error(f"Error: {e}. Check Mic and FFmpeg at C:\\ffmpeg\\bin")

    # Download feature for FDP
    if st.session_state.lecture_history:
        st.divider()
        st.download_button("📥 Download Class Transcript", st.session_state.lecture_history, file_name="lecture.txt")

# --- TAB 2: PDF Dual View ---
with tab2:
    st.subheader("PDF Side-by-Side Translator")
    uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_pdf:
        pdf_reader = PdfReader(uploaded_pdf)
        pdf_text = "".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        
        if st.button("Translate PDF"):
            # Translating first 2000 characters for demo
            trans_pdf = translator.translate(pdf_text[:2000], dest=languages[std_lang]["trans"]).text
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**English Original:**\n{pdf_text[:2000]}")
            with col2:
                st.success(f"**{std_lang} Translation:**\n{trans_pdf}")

# --- TAB 3: General Translation ---
with tab3:
    st.subheader("Text & Link Translator")
    user_input = st.text_area("Enter Text:")
    if user_input and st.button("Translate Now"):
        quick_trans = translator.translate(user_input, dest=languages[std_lang]["trans"]).text
        st.write(f"**Result:** {quick_trans}")