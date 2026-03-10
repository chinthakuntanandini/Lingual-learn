import streamlit as st
from streamlit_mic_recorder import mic_recorder
import ml_logic 

st.set_page_config(page_title="AI Learning Hub", layout="wide")

# Using Tabs to separate Teacher and Student roles clearly
tab1, tab2 = st.tabs(["👨‍🏫 Teacher Portal", "📖 Student Portal"])

# --- TEACHER PORTAL ---
with tab1:
    st.header("Start Your Lesson")
    st.write("Click below to record your lecture. AI will handle the rest!")
    
    # Recording component
    audio_data = mic_recorder(
        start_prompt="Record Lesson", 
        stop_prompt="Finish & Process", 
        key='teacher_mic'
    )

    if audio_data:
        with st.spinner("AI is preparing the lesson materials..."):
            # Teacher records -> AI instantly processes
            raw_text = ml_logic.speech_to_text(audio_data['bytes'])
            summary = ml_logic.generate_summary(raw_text)
            
            # Save to session so the Student Tab updates automatically
            st.session_state['processed_summary'] = summary
            st.success("Lesson processed! Students can now view it in their portal.")

# --- STUDENT PORTAL ---
with tab2:
    st.header("Your Learning Materials")
    
    if 'processed_summary' not in st.session_state:
        # If the teacher hasn't recorded yet, the student sees this:
        st.warning("Waiting for the teacher to finish the live lesson...")
    else:
        # Once the teacher stops recording, this section appears instantly
        selected_lang = st.selectbox("Select Language:", ["Telugu", "Hindi", "Tamil"])
        lang_map = {"Telugu": "te", "Hindi": "hi", "Tamil": "ta"}
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇬🇧 English Summary")
            st.info(st.session_state['processed_summary'])
            
        with col2:
            st.subheader(f"🌐 {selected_lang} Summary")
            translated = ml_logic.translate_text(st.session_state['processed_summary'], lang_map[selected_lang])
            st.success(translated)

        st.divider()
        st.subheader("📊 Lesson Concept Map")
        st.graphviz_chart('''
            digraph {
                node [shape=box, style=filled, color=lightblue]
                "Lesson Start" -> "Core Concepts" -> "Examples" -> "Quiz/Conclusion"
            }
        ''')
