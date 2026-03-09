import streamlit as st
import speech_recognition as sr
from googletrans import Translator
from fpdf import FPDF
import os
from pydub import AudioSegment
import io

# --- INITIALIZE ---
translator = Translator()
recognizer = sr.Recognizer()

# Application Interface Setup
st.set_page_config(page_title="AI Live Classroom", layout="wide")
st.title("🎙️ AI Live Bilingual Classroom Assistant")

# --- SIDEBAR: SETTINGS ---
st.sidebar.title("User Settings")
user_role = st.sidebar.radio("Select Your Role:", ["Teacher", "Student"])

languages = {"Telugu": "te", "Urdu": "ur", "Hindi": "hi"}
target_lang = st.sidebar.selectbox("Student Language", list(languages.keys()))
dest_code = languages[target_lang]

# --- MAIN LOGIC ---

if user_role == "Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    st.write("Click the microphone button below to start recording your lecture.")

    # LIVE AUDIO INPUT: Enables browser microphone
    audio_value = st.audio_input("Record your English lecture")

    if audio_value:
        st.info("Processing audio... Please wait.")
        try:
            # Convert recording to WAV format using Pydub
            audio_bytes = audio_value.read()
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
                # Speech to Text conversion
                english_text = recognizer.recognize_google(audio_data)
                
                # AI Translation to target language
                translation = translator.translate(english_text, dest=dest_code)
                translated_text = translation.text

                # Display Results in columns
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🇺🇸 English (Original)")
                    st.success(english_text)
                with col2:
                    st.subheader(f"🇮🇳 {target_lang} (Translated)")
                    st.info(translated_text)

                # Store data in Session State for Student View
                st.session_state['last_lecture'] = {
                    'text': translated_text,
                    'lang': target_lang
                }

        except Exception as e:
            st.error(f"Error: {e}. Please speak clearly and try again.")

else:
    # --- STUDENT VIEW ---
    st.header(f"🎓 Student Portal ({target_lang})")
    if 'last_lecture' in st.session_state:
        lecture = st.session_state['last_lecture']
        st.write(f"### Latest notes from teacher ({lecture['lang']}):")
        st.success(lecture['text'])
    else:
        st.warning("Waiting for the teacher to start the lecture...")

st.divider()
st.caption("AI-Powered Assistant for Inclusive Learning")
