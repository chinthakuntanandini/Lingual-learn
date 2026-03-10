import streamlit as st
import ml_logic  # Custom AI/ML logic for topic extraction
from googletrans import Translator
from fpdf import FPDF
from streamlit_mic_recorder import mic_recorder

# --- Application Setup ---
st.set_page_config(page_title="LinguaLearn AI Pro", layout="wide")
translator = Translator()

# --- Initialize Session State ---
# These keep data persistent across app reruns (switching roles, clicking buttons)
if 'final_summary' not in st.session_state:
    st.session_state['final_summary'] = ""
if 'broadcast_ready' not in st.session_state:
    st.session_state['broadcast_ready'] = False
if 'lecture_content' not in st.session_state:
    st.session_state['lecture_content'] = ""

# --- Role Selection Sidebar ---
st.sidebar.title("👤 User Control")
role = st.sidebar.radio("Select Your Role:", ["Teacher 👨‍🏫", "Student 📖"])

# -------------------------------------------
# --- TEACHER DASHBOARD ---
# -------------------------------------------
if role == "Teacher 👨‍🏫":
    st.header("👨‍🏫 Teacher Dashboard")
    
    # Step 1: Speech-to-Text Input
    st.write("🎙️ **Step 1: Record Lecture (Voice-to-Text)**")
    # This component captures audio and returns transcribed text
    audio = mic_recorder(start_prompt="Start Recording", stop_prompt="Stop Recording", key='recorder')
    
    # Display the text. If audio is recorded, it fills automatically; otherwise, manual typing is allowed.
    recorded_text = audio['text'] if audio and 'text' in audio else ""
    lecture_text = st.text_area("Lecture Content:", value=recorded_text, height=150)

    # Step 2: AI Processing
    if st.button("Generate AI Summary"):
        if lecture_text.strip():
            # Calling the AI model from ml_logic to identify the topic
            topic, _ = ml_logic.process_ai(lecture_text)
            
            st.session_state['lecture_content'] = lecture_text
            st.session_state['topic'] = topic
