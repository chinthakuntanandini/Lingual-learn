import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from deep_translator import GoogleTranslator
import io
import pydub
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF

# --- 1. Firebase Initialization ---
if not firebase_admin._apps:
    try:
        key_dict = dict(st.secrets["firebase"])
        if "private_key" in key_dict:
            cleaned_key = key_dict["private_key"].replace("\\n", "\n")
            if "-----BEGIN PRIVATE KEY-----" not in cleaned_key:
                cleaned_key = "-----BEGIN PRIVATE KEY-----\n" + cleaned_key
            if "-----END PRIVATE KEY-----" not in cleaned_key:
                cleaned_key = cleaned_key + "\n-----END PRIVATE KEY-----"
            key_dict["private_key"] = cleaned_key

        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")

try:
    db = firestore.client()
except Exception as e:
    st.error("Database connection failed.")

# --- 2. Multi-language PDF Generator ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'LinguaLearn AI Lecture Notes', 0, 1, 'C')
        self.ln(5)

# --- 3. UI Setup ---
st.set_page_config(page_title="LinguaLearn AI", layout="wide")
st.title("LinguaLearn: AI Inclusive Classroom 🎓")

languages = {
    "English": {"code": "en", "speech": "en-US"},
    "Telugu": {"code": "te", "speech": "te-IN"},
    "Urdu": {"code": "ur", "speech": "ur-PK"}
}

# --- 4. Sidebar Configuration ---
st.sidebar.header("Classroom Control")
role = st.sidebar.selectbox("User Role:", ["Teacher", "Student"])
recognizer = sr.Recognizer()

# --- 5. Teacher Interface ---
if role == "Teacher":
    st.subheader("👨‍🏫 Teacher Dashboard")
    st.info("The teacher speaks in English. Students can choose their own language.")
    
    audio_data = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="🛑 Stop & Broadcast", key='teacher_mic')

    if audio_data:
        try:
            audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio_data['bytes']))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio = recognizer.record(source)
                original_text = recognizer.recognize_google(audio, language="en-US")
                
                db.collection("classroom").document("live_lecture").set({
                    "original_text": original_text,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success(f"Broadcasted (English): {original_text}")
        except Exception as e:
            st.error(f"Processing Error: {e}")

# --- 6. Student Interface ---
else:
    st.subheader("🎓 Student Dashboard")
    student_needs = st.selectbox("Select your Preferred Language:", list(languages.keys()))

    doc_ref = db.collection("classroom").document("live_lecture")
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        raw_text = data.get('original_text', '')

        if raw_text:
            # Translation
            translated_text = GoogleTranslator(source='auto', target=languages[student_needs]["code"]).translate(raw_text)

            st.markdown(f"### 📖 Translated Lecture ({student_needs}):")
            st.info(translated_text)
            
            with st.expander("Show Original English"):
                st.write(raw_text)

            # PDF Generation with BOTH English and Translated Text
            if st.button("📄 Generate Bilingual PDF"):
                pdf = PDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                
                # Adding English Version
                pdf.set_text_color(0, 0, 255) # Blue for English
                pdf.multi_cell(0, 10, txt=f"English: {raw_text}")
                pdf.ln(5)
                
                # Adding Translated Version
                pdf.set_text_color(0, 128, 0) # Green for Translation
                # Note: FPDF requires custom fonts for Telugu/Urdu glyphs. 
                # This prints the string; if fonts are missing, it uses 'ignore' logic.
                pdf.multi_cell(0, 10, txt=f"{student_needs}: {translated_text}".encode('latin-1', 'ignore').decode('latin-1'))
                
                pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
                st.download_button(label="📥 Download PDF", data=pdf_output, file_name="bilingual_lecture.pdf", mime="application/pdf")
    else:
        st.warning("Waiting for the teacher...")

    if st.button("🔄 Sync Class"):
        st.rerun()
