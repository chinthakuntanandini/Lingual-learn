import streamlit as st
import speech_recognition as sr
from googletrans import Translator
from fpdf import FPDF
import os

# --- INITIALIZE ---
translator = Translator()
recognizer = sr.Recognizer()

# Application Interface
st.set_page_config(page_title="AI Bilingual Classroom", layout="wide")
st.title("🎙️ AI Bilingual Classroom Assistant")

# --- SIDEBAR: ROLE & LANGUAGE ---
st.sidebar.header("User Settings")
# This adds the Teacher/Student selection you were missing
user_role = st.sidebar.radio("Select Your Role:", ["Teacher", "Student"])

languages = {"Telugu": "te", "Urdu": "ur", "Hindi": "hi"}
target_lang = st.sidebar.selectbox("Select Student Language", list(languages.keys()))
dest_code = languages[target_lang]

# --- MAIN LOGIC ---

if user_role == "Teacher":
    st.subheader("👨‍🏫 Teacher Dashboard")
    st.write("Upload an English audio file to generate bilingual notes.")
    
    # Using File Uploader instead of Microphone to avoid the PyAudio error
    audio_file = st.file_uploader("Upload English Speech (WAV format)", type=["wav"])

    if st.button("🚀 Process & Translate") and audio_file is not None:
        try:
            with sr.AudioFile(audio_file) as source:
                st.info("Analyzing audio...")
                audio_data = recognizer.record(source)
                english_text = recognizer.recognize_google(audio_data)
                
                # AI Translation
                translation = translator.translate(english_text, dest=dest_code)
                translated_text = translation.text

                # Display on Screen
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 🇺🇸 English")
                    st.success(english_text)
                with col2:
                    st.markdown(f"### 🇮🇳 {target_lang}")
                    st.info(translated_text)

                # --- PDF GENERATION ---
                pdf = FPDF()
                pdf.add_page()
                font_path = "FreeSans.ttf"
                
                if os.path.exists(font_path):
                    pdf.add_font("FreeSans", "", font_path)
                    pdf.set_font("FreeSans", size=14)
                    pdf.cell(200, 10, txt="Classroom Lecture Notes", align='C', new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(10)
                    pdf.multi_cell(0, 10, txt=f"English: {english_text}")
                    pdf.ln(5)
                    pdf.multi_cell(0, 10, txt=f"{target_lang}: {translated_text}")
                    
                    pdf_output = pdf.output()
                    st.download_button(
                        label=f"📥 Download {target_lang} PDF",
                        data=bytes(pdf_output),
                        file_name="Bilingual_Notes.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("Note: 'FreeSans.ttf' not found. PDF will use standard fonts (no Telugu support).")

        except Exception as e:
            st.error(f"Processing Error: {e}")

else:
    # --- STUDENT VIEW ---
    st.subheader("🎓 Student Learning Portal")
    st.write(f"Your selected language is: **{target_lang}**")
    st.info("The teacher will provide the translated lecture notes here.")
    st.image("https://img.icons8.com/clouds/200/000000/education.png")

st.divider()
st.caption("AI-Powered Assistant for Inclusive Learning")
