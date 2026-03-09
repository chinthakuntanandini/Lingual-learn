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

# --- SHARED MEMORY LOGIC ---
# This dictionary will store the lecture text for ALL users
if 'shared_data' not in st.session_state:
    st.session_state['shared_data'] = {"english_text": ""}

# Function to update global text (Helper for sharing across sessions)
def update_lecture(text):
    st.session_state['shared_data']["english_text"] = text
    # For real-time multi-user apps, we often use a global variable or database
    # But for a single-app instance, this session check works during active use
    st.cache_resource.clear() 

# --- SIDEBAR: ROLE SELECTION ---
st.sidebar.title("User Access")
user_role = st.sidebar.radio("Select Your Role:", ["Teacher", "Student"])

# --- MAIN LOGIC ---

if user_role == "Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    st.write("Record your English lecture. It will be shared with all students.")

    audio_value = st.audio_input("Record your English lecture")

    if audio_value:
        st.info("Processing your speech... Please wait.")
        try:
            audio_bytes = audio_value.read()
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
                english_text = recognizer.recognize_google(audio_data)
                
                st.subheader("🇺🇸 Your Speech (English)")
                st.success(english_text)

                # Save to shared state
                st.session_state['shared_text'] = english_text

        except Exception as e:
            st.error(f"Error: {e}")

else:
    # --- STUDENT VIEW ---
    st.header("🎓 Student Portal")
    
    languages = {"Telugu": "te", "Urdu": "ur", "Hindi": "hi", "Tamil": "ta"}
    student_lang = st.selectbox("Select your preferred language:", list(languages.keys()))
    dest_code = languages[student_lang]

    # Check if there is recorded text from the teacher
    if 'shared_text' in st.session_state:
        english_content = st.session_state['shared_text']
        
        with st.spinner(f"Translating to {student_lang}..."):
            translation = translator.translate(english_content, dest=dest_code)
            translated_text = translation.text

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇺🇸 Original (English)")
            st.write(english_content)
        with col2:
            st.subheader(f"🇮🇳 Translation ({student_lang})")
            st.success(translated_text)
            
        # PDF Option
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Lecture Notes - {student_lang}", ln=True, align='C')
        pdf.multi_cell(0, 10, txt=f"English: {english_content}")
        
        st.download_button(
            label="📥 Download PDF",
            data=pdf.output(dest='S'),
            file_name=f"lecture_{student_lang}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Waiting for the teacher to record. (Tip: If teacher already recorded, click 'Student' again to refresh)")

st.divider()
st.caption("AI-Powered Assistant for Multi-Language Classrooms")
