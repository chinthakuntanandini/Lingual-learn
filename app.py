import streamlit as st
import ml_logic
from googletrans import Translator
from fpdf import FPDF
from streamlit_mic_recorder import mic_recorder # Install this via pip

translator = Translator()

st.set_page_config(page_title="LinguaLearn AI Pro", layout="wide")

st.markdown('<h1 style="text-align: center; color: #1976d2;">🎓 LinguaLearn AI: Advanced Classroom</h1>', unsafe_allow_html=True)

# Role Selection
st.sidebar.title("👤 User Control")
role = st.sidebar.radio("Select Your Role:", ["Teacher 👨‍🏫", "Student 📖"])

# Initialize Session States
if 'final_content' not in st.session_state:
    st.session_state['final_content'] = ""
if 'final_summary' not in st.session_state:
    st.session_state['final_summary'] = ""
if 'final_subject' not in st.session_state:
    st.session_state['final_subject'] = ""

# --- TEACHER DASHBOARD ---
if role == "Teacher 👨‍🏫":
    st.subheader("👨‍🏫 Teacher Dashboard")
    
    # 1. Voice to Text Feature
    st.write("🎙️ **Step 1: Record your lecture**")
    audio = mic_recorder(start_prompt="Click to Start Speaking", stop_prompt="Stop Recording", key='recorder')
    
    # Text input for manual correction or direct typing
    lecture_input = st.text_area("Lecture Transcript (Edit if needed):", 
                                value=audio['text'] if audio else "", 
                                height=150)

    if st.button("🔍 Step 2: Generate AI Analysis"):
        if lecture_input.strip():
            # Run AI Logic
            subject, _ = ml_logic.process_ai(lecture_input)
            st.session_state['final_subject'] = subject
            st.session_state['final_content'] = lecture_input
            # Initial AI Summary
            st.session_state['final_summary'] = f"The lecture focused on {subject}. Key points discussed include the fundamental concepts and practical applications of the topic."
        else:
            st.warning("Please record or type something first.")

    # 2. Teacher Edits the Summary
    if st.session_state['final_summary']:
        st.markdown("---")
        st.write("📝 **Step 3: Review & Edit Summary**")
        edited_summary = st.text_area("Final Summary (Teacher can modify this before students see it):", 
                                     value=st.session_state['final_summary'], height=100)
        
        if st.button("📡 Step 4: Final Broadcast to Students"):
            st.session_state['final_summary'] = edited_summary
            st.success("✅ Lecture and Edited Summary sent to students!")

# --- STUDENT HUB ---
else:
    st.subheader("📖 Student Learning Hub")
    st.sidebar.header("🌐 Translation Settings")
    target_lang = st.sidebar.selectbox("Preferred Language:", ["English", "Telugu", "Hindi", "Tamil"])
    lang_map = {"English": "en", "Telugu": "te", "Hindi": "hi", "Tamil": "ta"}

    if st.session_state['final_content']:
        st.info(f"📚 Subject: {st.session_state['final_subject']}")
        
        # Translation of Content & Summary
        translated_content = translator.translate(st.session_state['final_content'], dest=lang_map[target_lang]).text
        translated_summary = translator.translate(st.session_state['final_summary'], dest=lang_map[target_lang]).text

        col1, col2 = st.columns(2)
        with col1:
            st.write("📖 **Full Lecture**")
            st.success(translated_content)
        with col2:
            st.write("📝 **Teacher's Final Summary**")
            st.warning(translated_summary)

        # 3. PDF Generation (includes everything)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="LinguaLearn AI - Study Notes", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt=f"Subject: {st.session_state['final_subject']}\n\nSUMMARY:\n{st.session_state['final_summary']}\n\nFULL TRANSCRIPT:\n{st.session_state['final_content']}")
        
        st.download_button(
            label="📥 Download Study Material (PDF)",
            data=pdf.output(dest='S').encode('latin-1'),
            file_name="Class_Notes.pdf",
            mime="application/pdf"
        )
    else:
        st.write("Awaiting lecture from teacher...")

st.markdown("---")
st.caption("Developed by Nandini | AI/ML Driven Educational Solution")
