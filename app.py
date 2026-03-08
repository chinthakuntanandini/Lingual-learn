import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from googletrans import Translator
import io
import pydub
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. Firebase Initialization ---
# We check if the app is already initialized to avoid errors on refresh
if not firebase_admin._apps:
    try:
        # Load credentials from Streamlit Cloud Secrets (stored in the dashboard)
        secret_info = st.secrets["firebase_key"]
        key_dict = dict(secret_info)
        
        # Format the private key correctly by handling newline characters
        if "private_key" in key_dict:
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n").strip()
        
        # Use the credentials to initialize the Firebase Admin SDK
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        # Display an error message if the connection fails
        st.error(f"Firebase Connection Error: {e}")

# Create a Firestore client to interact with the database
db = firestore.client()

# --- 2. Page Configuration ---
st.set_page_config(page_title="LinguaLearn AI", layout="wide")
st.title("LinguaLearn: AI Inclusive Classroom 🎓")

# Define supported languages and their respective speech/translation codes
languages = {
    "English": {"speech": "en-US", "trans": "en"},
    "Telugu": {"speech": "te-IN", "trans": "te"},
    "Urdu": {"speech": "ur-PK", "trans": "ur"}
}

# --- 3. Sidebar Menu ---
st.sidebar.header("Classroom Settings")
# Select if the user is a Teacher or a Student
role = st.sidebar.selectbox("Select Role:", ["Teacher", "Student"])
# Select source and target languages
fdp_lang = st.sidebar.selectbox("Teacher Language:", list(languages.keys()))
std_lang = st.sidebar.selectbox("Student Language:", list(languages.keys()))

# Initialize translation and speech recognition objects
translator = Translator()
recognizer = sr.Recognizer()

# --- 4. Teacher Dashboard (Data Input) ---
if role == "Teacher":
    st.subheader("Teacher Dashboard (Broadcast Mode)")
    # Component to record audio directly from the browser microphone
    audio_data = mic_recorder(start_prompt="🎤 Start Class", stop_prompt="🛑 Stop Class", key='live_mic')

    if audio_data:
        try:
            # Convert the recorded audio bytes into a WAV format using pydub
            audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio_data['bytes']))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio = recognizer.record(source)
                # Step A: Convert Speech to Text (STT)
                original_text = recognizer.recognize_google(audio, language=languages[fdp_lang]["speech"])
                
                # Step B: Translate the Text to the selected student language
                translated_res = translator.translate(original_text, dest=languages[std_lang]["trans"])
                translated_text = translated_res.text

                # Step C: Upload results to Firebase Firestore
                db.collection("classroom").document("live_lecture").set({
                    "original": original_text,
                    "translated": translated_text,
                    "target_lang": std_lang,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })

                # Show success messages to the teacher
                st.success(f"Captured: {original_text}")
                st.success(f"Translated & Sent: {translated_text}")
        except Exception as e:
            st.error(f"Processing Error: {e}")

# --- 5. Student Dashboard (Data Output) ---
else:
    st.subheader("Student Dashboard (Live Learning)")
    # Fetch the latest lecture data from Firestore
    doc_ref = db.collection("classroom").document("live_lecture
