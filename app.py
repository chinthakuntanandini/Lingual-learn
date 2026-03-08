import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from deep_translator import GoogleTranslator  # Faster and no timeout issues
import io
import pydub
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF

# --- 1. Firebase Setup ---
if not firebase_admin._apps:
    try:
        secret_info = st.secrets["firebase_key"]
        key_dict = dict(secret_info)
        if "private_key" in key_dict:
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n").strip()
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")

db = firestore.client()

# --- 2. Multi-language PDF Setup ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'LinguaLearn AI Lecture Notes', 0, 1, 'C')
        self.ln(5)

# --- 3. Page Config ---
st.set_page_config(page_title="LinguaLearn AI", layout="wide")
st.title("LinguaLearn: AI Inclusive Classroom 🎓")

languages = {
    "English": {"code": "en", "speech": "en-US"},
    "Telugu": {"code": "te", "speech": "te-IN"},
    "Urdu": {"code": "ur", "speech": "ur-PK"}
}

# --- 4. Sidebar ---
st.sidebar.header("Classroom Control")
role = st.sidebar.selectbox("User Role:", ["Teacher", "Student"])
fdp_lang = st.sidebar.selectbox("Teacher Speaks In:", list(languages.keys()))
std_lang = st.sidebar.selectbox("Student Wants In:", list(languages.keys()))

recognizer = sr.Recognizer()

# --- 5. Teacher Interface ---
if role == "Teacher":
    st.subheader("Teacher Dashboard")
    st.info(f"Broadcast Mode Active: Speaking in {fdp_lang}")
    
    audio_data = mic_recorder(start_prompt="🎤 Start Class", stop_prompt="🛑 Stop Class", key='teacher_mic')

    if audio_data:
        try:
            # Process Audio
            audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio_data['bytes']))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio = recognizer.record(source)
                # Speech to Text
                original_text = recognizer.recognize_google(audio, language=languages[fdp_lang]["speech"])
                
                # Translation using deep_translator (No 60s timeout here)
                translated_text = GoogleTranslator(source='auto', target=languages[std_lang]["code"]).translate(original_text)

                # Save to Firebase
                db.collection("classroom").document("live_lecture").set({
                    "original": original_text,
                    "translated": translated_text,
                    "target_lang": std_lang,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })

                st.success(f"Sent: {translated_text}")
        except Exception as e:
            st.error(f"Error: {e}")

# --- 6. Student Interface ---
else:
    st.subheader("Student Dashboard")
    st.write("Fetching live updates from teacher...")

    # Fetch Data
    doc_ref = db.collection("classroom").document("live_lecture")
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        translated_msg = data.get('translated', 'No text yet.')
        
        st.markdown(f"### 📖 Translated Lecture:")
        st.info(translated_msg)

        # PDF Download Section
        if st.button("📄 Generate PDF"):
            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            # Note: Standard FPDF has limits with Telugu/Urdu fonts without extra files.
            # Using multi_cell to handle text.
            pdf.multi_cell(0, 10, txt=f"Lecture Content: {translated_msg}")
            
            pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
            st.download_button(label="📥 Download PDF", data=pdf_output, file_name="lecture.pdf", mime="application/pdf")
    else:
        st.warning("Waiting for the teacher to start speaking...")

    # Auto-Sync Button
    if st.button("🔄 Sync with Teacher"):
        st.rerun()
