import streamlit as st
import ml_logic
from googletrans import Translator
from fpdf import FPDF

# Initialize Translator
translator = Translator()

st.set_page_config(page_title="LinguaLearn AI Pro", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main-title { text-align: center; color: #1976d2; margin-bottom: 30px; }
    .role-container { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🎓 LinguaLearn AI: Advanced Classroom</h1>', unsafe_allow_html=True)

# --- STEP 1: ROLE SELECTION ---
# This ensures that the user chooses their role first
st.sidebar.title("👤 User Control")
role = st.sidebar.radio("Select Your Role:", ["Teacher 👨‍🏫", "Student 📖"])

# Initialize session state for the lecture content
if 'shared_lecture' not in st.session_state:
    st.session_state['shared_lecture'] = ""

# --- STEP 2: TEACHER INTERFACE ---
if role == "Teacher 👨‍🏫":
    st.subheader("👨‍🏫 Teacher Dashboard")
    st.info("Input your lecture below to broadcast it to students.")
    
    lecture_input = st.text_area("Live Lecture Input (English):", height=250, 
                                placeholder="Type or paste your lecture content here...")
    
    if st.button("📡 Broadcast to Students"):
        if lecture_input.strip():
            st.session_state['shared_lecture'] = lecture_input
            st.success("✅ Lecture broadcasted successfully!")
        else:
            st.warning("Please enter some content before broadcasting.")

# --- STEP 3: STUDENT INTERFACE ---
else:
    st.subheader("📖 Student Learning Hub")
    
    # Language settings only appear for students
    st.sidebar.markdown("---")
    st.sidebar.header("🌐 Translation Settings")
    target_lang = st.sidebar.selectbox("Preferred Language:", ["English", "Telugu", "Hindi", "Tamil", "Spanish"])
    lang_map = {"English": "en", "Telugu": "te", "Hindi": "hi", "Tamil": "ta", "Spanish": "es"}

    if st.session_state['shared_lecture']:
        # Run AI Logic
        subject, latency = ml_logic.process_ai(st.session_state['shared_lecture'])
        
        # Translation
        translated_text = translator.translate(st.session_state['shared_lecture'], dest=lang_map[target_lang]).text
        
        # UI Layout for student
        st.markdown(f"### Identified Topic: **{subject}**")
        
        col_orig, col_trans = st.columns(2)
        with col_orig:
            st.info("**Original Transcript (English)**")
            st.write(st.session_state['shared_lecture'])
            
        with col_trans:
            st.success(f"**Translated Content ({target_lang})**")
            st.write(translated_text)

        # Summary and PDF Section
        st.markdown("---")
        summary = f"Summary of {subject}: The lecture highlights key concepts starting with: {st.session_state['shared_lecture'][:100]}..."
        st.write("📝 **AI Summary:**", summary)

        # PDF Download
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="LinguaLearn AI Notes", ln=True, align='C')
        pdf.multi_cell(0, 10, txt=f"Subject: {subject}\n\nSummary: {summary}\n\nContent: {st.session_state['shared_lecture']}")
        
        st.download_button(
            label="📥 Download Notes as PDF",
            data=pdf.output(dest='S').encode('latin-1'),
            file_name="lecture_notes.pdf",
            mime="application/pdf"
        )
        
        # Sidebar metrics for AI performance
        st.sidebar.metric("AI Prediction Latency", f"{latency} sec")
    else:
        st.warning("Awaiting a live lecture from the teacher. Please stay tuned!")

st.markdown("---")
st.caption("Developed by Nandini | LinguaLearn AI Engine")
