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
    st.write("Click the microphone button to record.")

    audio_value = st.audio_input("Record your English lecture")

    if audio_value:
        st.info("Processing audio... Please wait.")
        try:
            audio_bytes = audio_value.read()
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
                english_text = recognizer.recognize_google(audio_data)
                
                translation = translator.translate(english_text, dest=dest_code)
                translated_text = translation.text

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🇺🇸 English")
                    st.success(english_text)
                with col2:
                    st.subheader(f"🇮🇳 {target_lang}")
                    st.info(translated_text)

                # --- PDF GENERATION (SIMPLE VERSION) ---
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="Classroom Lecture Notes", ln=True, align='C')
                pdf.ln(10)
                
                # Adding content to PDF
                pdf.multi_cell(0, 10, txt=f"English: {english_text}")
                pdf.ln(5)
                # Note: Standard PDF fonts don't support Telugu. 
                # This will save the English part clearly.
                pdf.multi_cell(0, 10, txt=f"Translated Content: {translated_text.encode('latin-1', 'replace').decode('latin-1')}")
                
                pdf_data = pdf.output(dest='S').encode('latin-1')
                
                st.download_button(
                    label="📥 Download PDF Notes",
                    data=pdf_data,
                    file_name="lecture_notes.pdf",
                    mime="application/pdf"
                )

                st.session_state['last_lecture'] = {'text': translated_text, 'lang': target_lang}

        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.header(f"🎓 Student Portal ({target_lang})")
    if 'last_lecture' in st.session_state:
        st.success(st.session_state['last_lecture']['text'])
