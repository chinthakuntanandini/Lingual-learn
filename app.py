import streamlit as st
import speech_recognition as sr
from googletrans import Translator
from pydub import AudioSegment
from gtts import gTTS
import io
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- INITIALIZE ---
translator = Translator()
recognizer = sr.Recognizer()

st.set_page_config(page_title="AI Live Classroom", layout="wide")
st.title("🎙️ AI Live Bilingual Classroom Assistant")

@st.cache_resource
def get_shared_data():
    return {"english_text": ""}

shared_storage = get_shared_data()

st.sidebar.title("User Access")
user_role = st.sidebar.radio("Select Your Role:", ["Teacher", "Student"])

if user_role == "Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    audio_value = st.audio_input("Record your English lecture")

    if audio_value:
        try:
            audio_bytes = audio_value.read()
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
                english_text = recognizer.recognize_google(audio_data)
                shared_storage["english_text"] = english_text
                st.success(f"Recorded: {english_text}")
        except Exception as e:
            st.error(f"Error: {e}")

else:
    st.header("🎓 Student Portal")
    languages = {"Telugu": "te", "Urdu": "ur", "Hindi": "hi", "Tamil": "ta"}
    student_lang = st.selectbox("Select your language:", list(languages.keys()))
    dest_code = languages[student_lang]

    english_content = shared_storage["english_text"]

    if english_content:
        translation = translator.translate(english_content, dest=dest_code)
        translated_text = translation.text

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇺🇸 English")
            st.write(english_content)
        with col2:
            st.subheader(f"🇮🇳 {student_lang}")
            st.success(translated_text)
            
            # Voice Output
            tts = gTTS(text=translated_text, lang=dest_code)
            tts_io = io.BytesIO()
            tts.write_to_fp(tts_io)
            st.audio(tts_io, format="audio/mp3")

        # --- NEW PDF GENERATION (ReportLab) ---
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        c.drawString(100, 800, "Class Lecture Notes")
        c.drawString(100, 780, f"English: {english_content}")
        
        # Note: True Unicode rendering in PDF requires uploading a .ttf font file to GitHub.
        # This version prevents the 'Character error' crash.
        c.drawString(100, 760, f"Language: {student_lang}")
        c.showPage()
        c.save()
        
        st.download_button(
            label="📥 Download PDF (English Notes)",
            data=buffer.getvalue(),
            file_name="lecture_notes.pdf",
            mime="application/pdf"
        )
        st.info("Note: For regional languages in PDF, please copy text from the screen.")
    else:
        st.warning("Waiting for teacher...")

st.divider()
st.caption("AI-Powered Assistant for Multi-Language Classrooms")
