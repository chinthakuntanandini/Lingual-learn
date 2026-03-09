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

# --- SIDEBAR: ROLE SELECTION ---
st.sidebar.title("User Access")
user_role = st.sidebar.radio("Select Your Role:", ["Teacher", "Student"])

# --- MAIN LOGIC ---

if user_role == "Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    st.write("Record your English lecture below. Students will choose their own translation language.")

    # Microphone input
    audio_value = st.audio_input("Record your English lecture")

    if audio_value:
        st.info("Processing your speech... Please wait.")
        try:
            # Audio processing logic
            audio_bytes = audio_value.read()
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
                english_text = recognizer.recognize_google(audio_data)
                
                # Show teacher what they said in English
                st.subheader("🇺🇸 Your Speech (English)")
                st.success(english_text)

                # IMPORTANT: Save ONLY English text for the session
                st.session_state['original_english'] = english_text

        except Exception as e:
            st.error(f"Error: {e}. Please try again.")

else:
    # --- STUDENT VIEW ---
    st.header("🎓 Student Portal")
    
    # Student selects their OWN language here
    languages = {"Telugu": "te", "Urdu": "ur", "Hindi": "hi", "Tamil": "ta"}
    student_lang = st.selectbox("Select your preferred language:", list(languages.keys()))
    dest_code = languages[student_lang]

    if 'original_english' in st.session_state:
        english_content = st.session_state['original_english']
        
        # Translate the saved English text to the student's chosen language
        with st.spinner(f"Translating to {student_lang}..."):
            translation = translator.translate(english_content, dest=dest_code)
            translated_text = translation.text

        # Display results to student
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇺🇸 Original (English)")
            st.write(english_content)
        with col2:
            st.subheader(f"🇮🇳 Translation ({student_lang})")
            st.success(translated_text)
            
        # PDF Option for Student
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Lecture Notes - {student_lang}", ln=True, align='C')
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt=f"English: {english_content}")
        # PDF encoding fix
        safe_translated = translated_text.encode('utf-8', 'ignore').decode('latin-1', 'replace')
        pdf.multi_cell(0, 10, txt=f"Notes: {safe_translated}")
        
        st.download_button(
            label="📥 Download Notes as PDF",
            data=pdf.output(dest='S'),
            file_name=f"lecture_{student_lang}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Waiting for the teacher to record the lecture. Please stay tuned.")

st.divider()
st.caption("AI-Powered Assistant for Multi-Language Classrooms")
