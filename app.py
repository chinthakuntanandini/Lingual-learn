import streamlit as st
import ml_logic
import time
from googletrans import Translator # library for multi-language translation
from fpdf import FPDF # library for generating PDF documents

# Initialize the Google Translate API
translator = Translator()

# Set up page layout and title
st.set_page_config(page_title="LinguaLearn AI Pro", layout="wide")

# Custom CSS for enhanced UI design
st.markdown("""
    <style>
    .teacher-box { background-color: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #1976d2; }
    .student-box { background-color: #f1f8e9; padding: 20px; border-radius: 10px; border-left: 5px solid #388e3c; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 LinguaLearn AI: Advanced Classroom")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Student Settings")
# Allow students to choose their preferred language for translation
target_lang = st.sidebar.selectbox("Choose Your Language", ["English", "Telugu", "Hindi", "Tamil", "Spanish"])
# Mapping display names to Google Translate language codes
lang_map = {"English": "en", "Telugu": "te", "Hindi": "hi", "Tamil": "ta", "Spanish": "es"}

# --- MAIN INTERFACE LAYOUT ---
col1, col2 = st.columns(2)

with col1:
    # Teacher Interface
    st.markdown('<div class="teacher-box"><h3>👨‍🏫 Teacher Panel</h3></div>', unsafe_allow_html=True)
    
    # Feature: Real-time Speech-to-Text Simulation
    st.info("🎙️ Mic Status: Active (Listening for Speech...)")
    lecture_text = st.text_area("Teacher's Live Lecture Input:", height=200, 
                               placeholder="Start speaking or type the lecture content here...")
    
    # Trigger AI processing and student broadcast
    broadcast = st.button("📡 Broadcast & Analyze")

with col2:
    # Student Interface
    st.markdown('<div class="student-box"><h3>📖 Student View</h3></div>', unsafe_allow_html=True)
    
    if broadcast and lecture_text:
        # Step 1: Execute Machine Learning models (Classification & Regression)
        # Identifies the subject and predicts the processing delay
        subject, latency = ml_logic.process_ai(lecture_text)
        
        # Step 2: Perform Real-time Translation to the selected target language
        translated = translator.translate(lecture_text, dest=lang_map[target_lang]).text
        
        # Step 3: Display identified subject and translated lecture content
        st.subheader(f"Topic: {subject}")
        st.write(f"**Lecture Content in {target_lang}:**")
        st.success(translated)
        
        # Step 4: Generate a Final Summary of the lecture
        st.markdown("---")
        st.subheader("📝 AI-Generated Summary")
        summary = f"This session covered the core principles of {subject}. Highlights: {lecture_text[:60]}..."
        st.write(summary)
        
        # Step 5: PDF Generation and Download Feature
        # Creating a PDF document with subject, original text, and summary
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="LinguaLearn AI - Lecture Notes", ln=True, align='C')
        pdf.ln(10) # Line break
        # Using multi_cell to handle long strings of text
        pdf.multi_cell(0, 10, txt=f"Subject: {subject}\n\nOriginal Transcript: {lecture_text}\n\nLecture Summary: {summary}")
        
        # Provide a download button for the generated PDF
        st.download_button(
            label="📥 Download Notes as PDF",
            data=pdf.output(dest='S').encode('latin-1'),
            file_name="lecture_notes.pdf",
            mime="application/pdf"
        )
        
        # Display AI performance metrics in the sidebar
        st.sidebar.metric("AI Processing Latency", f"{latency} sec")
        st.sidebar.write(f"Model: Random Forest & Linear Regression")
    else:
        st.write("Awaiting broadcast from the teacher's panel...")

# Footer credit
st.markdown("---")
st.caption("Developed by Nandini | AI/ML Driven Educational Solution")
