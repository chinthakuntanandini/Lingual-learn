import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS  
from PyPDF2 import PdfReader
import io
import pydub
import os

# --- 1. Page Setup ---
st.set_page_config(page_title="LinguaLearn AI", layout="wide")
st.title("LinguaLearn: AI Inclusive Classroom 🎓")

# Initialize session state for lecture history
if "lecture_history" not in st.session_state:
    st.session_state.lecture_history = ""

# --- 2. Sidebar Settings ---
st.sidebar.header("Classroom Settings")

# ROLE SELECTION (Crucial Change)
role = st.sidebar.selectbox("Select Role", ["Teacher", "Student"])

# Language mapping
languages = {
    "English": {"speech": "en-US", "trans": "en"},
    "Telugu": {"speech": "te-IN", "trans": "te"},
    "Urdu": {"speech": "ur-PK", "trans": "ur"}
}

fdp_lang = st.sidebar.selectbox("Teacher Language:", list(languages.keys()))
std_lang = st.sidebar.selectbox("Student Language:", list(languages.keys()))

translator = Translator()
recognizer = sr.Recognizer()

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["🎙️ Live Class", "📄 PDF Translate", "🔗 Link/Text"])

# --- TAB 1: Live Class (Role Based Access) ---
with tab1:
    st.subheader("Live Audio Translation")
    
    if role == "Teacher":
        st.info(f"Teacher Mode: Speaking in {fdp_lang}")
        # Mic is ONLY visible to the Teacher
        audio_data = mic_recorder(start_prompt="🎤 Start Class", stop_prompt="🛑 Stop Class", key='live_mic')
        
        if audio_data:
            try:
                audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio_data['bytes']))
                wav_io = io.BytesIO()
                audio_segment.export(wav_io, format="wav")
                wav_io.seek(0)
                
                with sr.AudioFile(wav_io) as source:
                    audio = recognizer.record(source)
                    original_text = recognizer.recognize_google(audio, language=languages[fdp_lang]["speech"])
                    
                    translated_res = translator.translate(original_text, dest=languages[std_lang]["trans"])
                    translated_text = translated_res.text
                    
                    st.write(f"**Original ({fdp_lang}):** {original_text}")
                    st.success(f"**Translated ({std_lang}):** {translated_text}")
                    
                    # Voice Output
                    tts = gTTS(text=translated_text, lang=languages[std_lang]["trans"])
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                    
                    # Update History
                    st.session_state.lecture_history += f"Teacher: {original_text}\nStudent ({std_lang}): {translated_text}\n\n"
            except Exception as e:
                st.error("Microphone error. Please ensure FFmpeg is installed via packages.txt")
    
    else:
        # Student View: No Mic, only History
        st.warning("Student Mode: Listening for Teacher's updates...")
        if st.session_state.lecture_history:
            st.write("**Live Class Transcript:**")
            st.text_area("Live Feed", st.session_state.lecture_history, height=400)
        else:
            st.info("The teacher hasn't started the lecture yet.")

# --- TAB 2: PDF Dual View (Available to Both) ---
with tab2:
    st.subheader("PDF Side-by-Side Translator")
    uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_pdf:
        pdf_reader = PdfReader(uploaded_pdf)
        pdf_text = "".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        
        if st.button("Translate PDF"):
            trans_pdf = translator.translate(pdf_text[:2000], dest=languages[std_lang]["trans"]).text
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Original Text:**\n{pdf_text[:2000]}")
            with col2:
                st.success(f"**{std_lang} Translation:**\n{trans_pdf}")

# --- TAB 3: General Translation ---
with tab3:
    st.subheader("Text & Link Translator")
    user_input = st.text_area("Enter Text:")
    if user_input and st.button("Translate Now"):
        quick_trans = translator.translate(user_input, dest=languages[std_lang]["trans"]).text
        st.write(f"**Result:** {quick_trans}")

# Transcript Download
if st.session_state.lecture_history:
    st.sidebar.divider()
    st.sidebar.download_button("📥 Download Transcript", st.session_state.lecture_history, file_name="lecture.txt")
