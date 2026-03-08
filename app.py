import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from googletrans import Translator
import io
import pydub
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. Firebase Initialization ---
if not firebase_admin._apps:
    try:
        # Load credentials from Streamlit Cloud Secrets
        secret_info = st.secrets["firebase_key"]
        key_dict = dict(secret_info)
        
        # Format the private key correctly
        if "private_key" in key_dict:
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n").strip()
        
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")

# Create a Firestore client
db = firestore.client()

# --- 2. Page Configuration ---
st.set_page_config(page_title="LinguaLearn AI", layout="wide")
st.title("LinguaLearn: AI Inclusive Classroom 🎓")

# Supported languages
languages = {
    "English": {"speech": "en-US", "trans": "en"},
    "Telugu": {"speech": "te-IN", "trans": "te"},
    "Urdu": {"speech": "ur-PK", "trans": "ur"}
}

# --- 3. Sidebar Menu ---
st.sidebar.header("Classroom Settings")
role = st.sidebar.selectbox("Select Role:", ["Teacher", "Student"])
fdp_lang = st.sidebar.selectbox("Teacher Language:", list(languages.keys()))
std_lang = st.sidebar.selectbox("Student Language:", list(languages.keys()))

translator = Translator()
recognizer = sr.Recognizer()

# --- 4. Teacher Dashboard ---
if role == "Teacher":
    st.subheader("Teacher Dashboard (Broadcast Mode)")
    audio_data = mic_recorder(start_prompt="🎤 Start Class", stop_prompt="🛑 Stop Class", key='live_mic')

    if audio_data:
        try:
            audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio_data['bytes']))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio = recognizer.record(source)
                # Convert Speech to Text
                original_text = recognizer.recognize_google(audio, language=languages[fdp_lang]["speech"])
                
                # Translate the Text
                translated_res = translator.translate(original_text, dest=languages[std_lang]["trans"])
                translated_text = translated_res.text

                # Upload to Firebase
                db.collection("classroom").document("live_lecture").set({
                    "original": original_text,
                    "translated": translated_text,
                    "target_lang": std_lang
                })

                st.success(f"Captured: {original_text}")
                st.success(f"Translated & Sent: {translated_text}")
        except Exception as e:
            st.error(f"Processing Error: {e}")

# --- 5. Student Dashboard ---
else:
    st.subheader("Student Dashboard (Live Learning)")
    # FIXED LINE BELOW: Added missing quote and parenthesis
    doc_ref = db.collection("classroom").document("live_lecture")
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        st.markdown(f"### 📖 Live Translation ({std_lang}):")
        st.write(data.get('translated', 'Waiting for teacher...'))
    else:
        st.info("The teacher has not started yet.")
    
    if st.button("🔄 Sync with Teacher"):
        st.rerun()
