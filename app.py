import streamlit as st
from streamlit_mic_recorder import mic_recorder
import ml_logic 

# Setting up page title and layout
st.set_page_config(page_title="Teacher-Student AI Assistant", layout="wide")

st.title("👨‍🏫 Teacher-Student Learning Hub")

# --- TEACHER SECTION ---
st.header("🎤 Teacher's Lecture (Recording)")
audio_data = mic_recorder(start_prompt="Start Recording Class", stop_prompt="End Class", key='recorder')

if audio_data:
    with st.spinner("AI is analyzing the lecture..."):
        # Converting speech to full text
        full_text = ml_logic.process_ai(audio_data['bytes'])
        st.session_state['lecture_text'] = full_text
        
        # Generating English Summary
        st.session_state['english_summary'] = ml_logic.summarize_text(full_text)

# --- STUDENT SECTION ---
if 'english_summary' in st.session_state:
    st.write("---")
    st.header("📖 Student's Learning View")
    
    # 1. Language Selection
    student_lang = st.selectbox("Choose your Language (మీ భాషను ఎంచుకోండి):", 
                                ["Telugu (తెలుగు)", "Hindi (हिंदी)", "Tamil (தமிழ்)", "Kannada (కన్నడ)"])
    
    lang_map = {"Telugu (తెలుగు)": "te", "Hindi (हिंदी)": "hi", "Tamil (தமிழ்)": "ta", "Kannada (కన్నడ)": "kn"}
    target_code = lang_map[student_lang]

    # 2. Dual Language Summary Display
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🇬🇧 English Summary")
        st.info(st.session_state['english_summary'])

    with col2:
        st.subheader(f"🌐 {student_lang} Summary")
        # Translating the summary
        translated_summary = ml_logic.translate_summary(st.session_state['english_summary'], target_code)
        st.success(translated_summary)

    # 3. Lesson Flow Diagram
    st.write("---")
    st.subheader("📊 Lesson Flow Diagram")
    
    st.graphviz_chart(f'''
        digraph {{
            node [shape=box, style=filled, color=lightblue, fontname="Arial"]
            "Start Class" -> "Key Concepts"
            "Key Concepts" -> "In-depth Examples"
            "In-depth Examples" -> "Final Summary"
        }}
    ''')

st.write("---")
st.caption("Common English is provided for better technical understanding.")
