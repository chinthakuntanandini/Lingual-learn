import streamlit as st
from streamlit_mic_recorder import mic_recorder
import ml_logic  # Custom module containing your AI and translation logic

# Page configuration for a wide-screen layout and custom browser tab title
st.set_page_config(page_title="Teacher-Student AI Hub", layout="wide")

st.title("👨‍🏫 Teacher-Student AI Learning Hub")

# --- TEACHER SECTION ---
# This part allows the teacher to record the live lecture
st.header("🎤 Teacher's Recording Section")

# mic_recorder component creates a button that captures audio bytes
audio_data = mic_recorder(
    start_prompt="Record Lesson (పాఠాన్ని రికార్డ్ చేయండి)", 
    stop_prompt="Stop Recording (రికార్డింగ్ ఆపండి)", 
    key='recorder'
)

# Trigger AI processing only if audio has been successfully recorded
if audio_data:
    with st.spinner("AI is analyzing the lecture..."):
        # 1. Convert the raw audio bytes into text using Speech-to-Text (STT)
        raw_text = ml_logic.speech_to_text(audio_data['bytes'])
        
        # 2. Use a Large Language Model (LLM) to generate a concise summary
        # Store the result in session_state so it persists across UI interactions
        st.session_state['lecture_summary'] = ml_logic.generate_summary(raw_text)

# --- STUDENT SECTION ---
# This section only appears once the summary is ready in the session state
if 'lecture_summary' in st.session_state:
    st.divider()
    st.header("📖 Student View (విద్యార్థి విభాగం)")
    
    # Language selector for students to choose their preferred native language
    selected_lang = st.selectbox(
        "Choose your language (మీ భాషను ఎంచుకోండి):", 
        ["Telugu (తెలుగు)", "Hindi (हिंदी)", "Tamil (தமிழ்)"]
    )
    
    # Map the display name to ISO language codes for the translation API
    lang_mapping = {
        "Telugu (తెలుగు)": "te", 
        "Hindi (हिंदी)": "hi", 
        "Tamil (தமிழ்)": "ta"
    }
    lang_code = lang_mapping[selected_lang]

    # Create two columns to show English and translated summaries side-by-side
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🇬🇧 English Summary")
        # Display the original English summary in an info box
        st.info(st.session_state['lecture_summary'])

    with col2:
        st.subheader(f"🌐 {selected_lang} Summary")
        # Translate the summary into the student's chosen language via ml_logic
        translated = ml_logic.translate_text(st.session_state['lecture_summary'], lang_code)
        st.success(translated)

    # --- VISUALIZATION SECTION ---
    # Display a dynamic flowchart of the lesson structure using Graphviz
    st.subheader("📊 Lesson Structure (పాఠం క్రమం)")
    
    
    
    st.graphviz_chart('''
        digraph {
            node [shape=box, style=filled, color=lightyellow, fontname="Arial"]
            "Introduction" -> "Core Topic" -> "Examples" -> "Conclusion"
        }
    ''')
