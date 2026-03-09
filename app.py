import streamlit as st
import speech_recognition as sr
from googletrans import Translator
from fpdf import FPDF
from pydub import AudioSegment
from gtts import gTTS
import io

# --- INITIALIZE ---
translator = Translator()
recognizer = sr.Recognizer()

# Application Interface Setup
st.set_page_config(page_title="AI Live Classroom", layout="wide")
st.title("🎙️ AI Live Bilingual Classroom Assistant")

# --- GLOBAL DATA SHARING ---
@st.cache_resource
def get_shared_data():
    return {"english_text": ""}

shared_storage = get_shared_data()

# --- SIDEBAR ---
st.sidebar.title("User Access")
user_role = st.sidebar.radio("Select Your Role:", ["Teacher", "Student"])

# --- MAIN LOGIC ---

if user_role == "Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    st.write("Record your English lecture. It will be shared with all students.")

    audio_value = st.audio_input("Record your English lecture")

    if audio_value:
        st.info("Processing... Please wait.")
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
                
                st.subheader("🇺🇸 Your Speech (English)")
                st.success(english_text)
                st.info("✅ Shared with students.")

        except Exception as e:
            st.error(f"Error: {e}")

else:
    # --- STUDENT VIEW ---
    st.header("🎓 Student Portal")
    
    languages = {"Telugu": "te", "Urdu": "ur", "Hindi": "hi", "Tamil": "ta"}
    student_lang = st.selectbox("Select your language:", list(languages.keys()))
    dest_code = languages[student_lang]

    english_content = shared_storage["english_text"]

    if english_content:
        with st.spinner(f"Translating to {student_lang}..."):
            translation = translator.translate(english_content, dest=dest_code)
            translated_text = translation.text

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇺🇸 English")
            st.write(english_content)
        with col2:
            st.subheader(f"🇮🇳 {student_lang}")
            st.success(translated_text)
            
            # --- VOICE (TEXT TO SPEECH) ---
            st.write("🔊 Listen to the translation:")
            try:
                tts = gTTS(text=translated_text, lang=dest_code)
                tts_io = io.BytesIO()
                tts.write_to_fp(tts_io)
                st.audio(tts_io, format="audio/mp3")
            except Exception as tts_err:
                st.error("Could not generate voice audio.")
            
        # PDF Option
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Lecture Notes", ln=True, align='C')
            pdf.multi_cell(0, 10, txt=f"English: {english_content}")
            st.download_button(label="📥 Download PDF", data=bytes(pdf.output()), file_name="notes.pdf")
        except:
            pass
        
    else:
        st.warning("Waiting for the teacher to record...")
        if st.button("🔄 Refresh"):
            st.rerun()

st.divider()
st.caption("AI-Powered Assistant for Multi-Language Classrooms")
