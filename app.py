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
st.write("Real-time English to Bilingual Speech Translation")

# --- SIDEBAR ---
languages = {"Telugu": "te", "Urdu": "ur", "Hindi": "hi"}
target_lang = st.sidebar.selectbox("Select Student Language", list(languages.keys()))
dest_code = languages[target_lang]

# --- MAIN LOGIC ---
if st.button("🔴 Start Recording"):
    with sr.Microphone() as source:
        st.info("Listening... Please speak in English.")
        # Calibration for background noise
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            # 1. Capture English Speech
            audio_data = recognizer.listen(source, timeout=5)
            english_text = recognizer.recognize_google(audio_data)
            
            # 2. AI Translation
            translation = translator.translate(english_text, dest=dest_code)
            translated_text = translation.text

            # Display on Screen
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("English (Original)")
                st.success(english_text)
            with col2:
                st.subheader(f"{target_lang} (Translated)")
                st.info(translated_text)

            # --- 3. BILINGUAL PDF GENERATION ---
            pdf = FPDF()
            pdf.add_page()
            
            # FreeSans.ttf is required for Telugu/Urdu character support
            font_path = "FreeSans.ttf"
            
            if os.path.exists(font_path):
                # NOTE: 'uni=True' is removed as it's not needed in latest fpdf2
                pdf.add_font("FreeSans", "", font_path)
                pdf.set_font("FreeSans", size=14)
                
                # Header
                pdf.cell(200, 10, txt="Classroom Lecture Notes", align='C', new_x="LMARGIN", new_y="NEXT")
                pdf.ln(10)
                
                # Bilingual content
                pdf.multi_cell(0, 10, txt=f"English: {english_text}")
                pdf.ln(5)
                pdf.multi_cell(0, 10, txt=f"{target_lang}: {translated_text}")
                
                # Generate PDF binary data directly to memory
                pdf_output = pdf.output()
                
                # 4. DOWNLOAD BUTTON
                st.download_button(
                    label=f"📥 Download {target_lang} PDF",
                    data=bytes(pdf_output),
                    file_name="Bilingual_Notes.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Error: 'FreeSans.ttf' font file not found in the project folder.")

        except Exception as e:
            st.error(f"Processing Error: {e}")

st.divider()
st.caption("AI-Powered Assistant for Inclusive Learning")
