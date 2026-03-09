import streamlit as st
import speech_recognition as sr
from googletrans import Translator
from fpdf import FPDF
from pydub import AudioSegment
import io

# --- INITIALIZE ---
translator = Translator()
recognizer = sr.Recognizer()

# Application Interface Setup
st.set_page_config(page_title="AI Live Classroom", layout="wide")
st.title("🎙️ AI Live Bilingual Classroom Assistant")

# --- GLOBAL DATA SHARING ---
# This ensures that text recorded by the teacher is shared with all student sessions
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
    st.write("Record your English lecture. It will be shared with all students globally.")

    # Audio input for live recording
    audio_value = st.audio_input("Record your English lecture")

    if audio_value:
        st.info("Processing... Please wait.")
        try:
            # Converting recorded audio to WAV for recognition
            audio_bytes = audio_value.read()
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
                english_text = recognizer.recognize_google(audio_data)
                
                # Saving the recognized text to shared server memory
                shared_storage["english_text"] = english_text
                
                st.subheader("🇺🇸 Your Speech (English)")
                st.success(english_text)
                st.info("✅ This text is now visible to all students.")

        except Exception as e:
            st.error(f"Error: {e}")

else:
    # --- STUDENT VIEW ---
    st.header("🎓 Student Portal")
    
    # Students select their preferred language for translation
    languages = {"Telugu": "te", "Urdu": "ur", "Hindi": "hi", "Tamil": "ta"}
    student_lang = st.selectbox("Select your language:", list(languages.keys()))
    dest_code = languages[student_lang]

    # Retrieving recorded text from shared memory
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
            
        # PDF Export Logic
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Lecture Notes - {student_lang}", ln=True, align='C')
        pdf.multi_cell(0, 10, txt=f"English Content: {english_content}")
        
        # Binary PDF output for Streamlit download button
        pdf_data = pdf.output(dest='S').encode('latin-1', 'ignore')
        
        st.download_button(
            label="📥 Download PDF", 
            data=pdf_data, 
            file_name="lecture_notes.pdf",
            mime="application/pdf"
        )
        
    else:
        st.warning("Waiting for the teacher to record... If the teacher already finished, please refresh.")
        if st.button("🔄 Refresh for New Notes"):
            st.rerun()

st.divider()
st.caption("AI-Powered Assistant for Multi-Language Classrooms")
