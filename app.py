import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from deep_translator import GoogleTranslator
import io
import pydub
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF

# --- 1. Firebase Initialization (Fix for InvalidByte/PEM Error) ---
if not firebase_admin._apps:
    try:
        # Fetch the secret dictionary from Streamlit
        key_dict = dict(st.secrets["firebase_key"])
        
        # CLEANUP LOGIC: This fixes the "Unable to load PEM file" error
        # It ensures that \n characters are treated as real newlines
        if "private_key" in key_dict:
            cleaned_key = key_dict["private_key"].replace("\\n", "\n")
            # Ensure the key is wrapped correctly if quotes were stripped
            if "-----BEGIN PRIVATE KEY-----" not in cleaned_key:
                cleaned_key = "-----BEGIN PRIVATE KEY-----\n" + cleaned_key
            if "-----END PRIVATE KEY-----" not in cleaned_key:
                cleaned_key = cleaned_key + "\n-----END PRIVATE KEY-----"
            
            key_dict["private_key"] = cleaned_key

        # Initialize the app with the cleaned dictionary
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")

# Initialize Firestore Client
try:
    db = firestore.client()
except Exception as e:
    st.error("Database connection failed. Please check your Secrets configuration.")

# --- 2. Multi-language PDF Generator ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'LinguaLearn AI Lecture Notes', 0, 1, 'C')
        self.ln(5)

# --- 3. UI Setup ---
st.set_page_config(page_title="LinguaLearn AI", layout="wide")
st.title("LinguaLearn: AI Inclusive Classroom 🎓")

# Language mapping for Speech Recognition and Translation
languages = {
    "English": {"code": "en", "speech": "en-US"},
    "Telugu": {"code": "te", "speech": "te-IN"},
    "Urdu": {"code": "ur", "speech": "ur-PK"}
}

# --- 4. Sidebar Configuration ---
st.sidebar.header("Classroom Control")
role = st.sidebar.selectbox("User Role:", ["Teacher", "Student"])
fdp_lang = st.sidebar.selectbox("Teacher Speaks In:", list(languages.keys()))
std_lang = st.sidebar.selectbox("Student Wants In:", list(languages.keys()))

recognizer = sr.Recognizer()

# --- 5. Teacher Interface ---
if role == "Teacher":
    st.subheader("Teacher Dashboard")
    st.info(f"Broadcast Mode: Recording in {fdp_lang}...")
    
    # Capture audio from the microphone
    audio_data = mic_recorder(start_prompt="🎤 Start Class", stop_prompt="🛑 Stop Class", key='teacher_mic')

    if audio_data:
        try:
            # Convert audio bytes to WAV format
            audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio_data['bytes']))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio = recognizer.record(source)
                # Speech to Text (STT)
                original_text = recognizer.recognize_google(audio, language=languages[fdp_lang]["speech"])
                
                # Translation using Deep Translator (solves the 60s timeout issue)
                translated_text = GoogleTranslator(source='auto', target=languages[std_lang]["code"]).translate(original_text)

                # Sync data to Firebase Firestore
                db.collection("classroom").document("live_lecture").set({
                    "original": original_text,
                    "translated": translated_text,
                    "target_lang": std_lang,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })

                st.success(f"Broadcasted: {translated_text}")
        except Exception as e:
            st.error(f"Processing Error: {e}")

# --- 6. Student Interface ---
else:
    st.subheader("Student Dashboard")
    st.write("Listening for live updates...")

    # Pull the latest data from the Cloud Database
    doc_ref = db.collection("classroom").document("live_lecture")
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        translated_msg = data.get('translated', 'No text captured yet.')
        
        st.markdown(f"### 📖 Translated Lecture ({std_lang}):")
        st.info(translated_msg)

        # PDF Export Logic
        if st.button("📄 Generate PDF"):
            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            # Standard PDF libraries require custom fonts for Telugu/Urdu;
            # This will print the translated string to the document.
            pdf.multi_cell(0, 10, txt=f"Lecture Content: {translated_msg}")
            
            pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
            st.download_button(label="📥 Download PDF", data=pdf_output, file_name="lecture.pdf", mime="application/pdf")
    else:
        st.warning("Teacher is offline. Please wait for the lecture to start.")

    # Manual refresh button to trigger a rerun and fetch new data
    if st.button("🔄 Sync with Teacher"):
        st.rerun()
