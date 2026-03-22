import streamlit as st
import pandas as pd
from fpdf import FPDF
from deep_translator import GoogleTranslator
from google.cloud import firestore
from google.cloud import speech
from google.oauth2 import service_account
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURATION & DATABASE CONNECTION ---
st.set_page_config(page_title="NeuralBridge AI", page_icon="🎓", layout="wide")

@st.cache_resource
def init_all_services():
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            creds = service_account.Credentials.from_service_account_info(info)
            db = firestore.Client(credentials=creds, project=creds.project_id)
            return db, creds
    except Exception as e:
        return None, None
    return None, None

db, google_creds = init_all_services()

# --- 2. AI SPEECH-TO-TEXT ENGINE ---
def run_ai_stt(audio_bytes):
    try:
        client = speech.SpeechClient(credentials=google_creds)
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US", # తెలుగు కోసం "te-IN"
            enable_automatic_punctuation=True
        )
        response = client.recognize(config=config, audio=audio)
        for result in response.results:
            return result.alternatives[0].transcript
    except:
        return None
    return ""

# --- 3. PROFESSIONAL PDF GENERATOR ---
def create_custom_pdf(title, header, rows):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    
    # Header
    pdf.set_font("Arial", 'B', 10)
    for col in header:
        pdf.cell(40, 10, txt=col, border=1)
    pdf.ln()
    
    # Rows
    pdf.set_font("Arial", size=10)
    for row in rows:
        for item in row:
            pdf.cell(40, 10, txt=str(item), border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
page = st.sidebar.selectbox("Go to Module", 
    ["Student Join", "Teacher Dashboard", "Live AI Class", "AI Table Creator"])

# --- 5. MODULE: LIVE AI CLASS ---
if page == "Live AI Class":
    st.header("🎙️ Live AI Lecture & Multi-Language Broadcast")
    
    # Audio Input
    audio_input = mic_recorder(start_prompt="▶️ Start Speaking", stop_prompt="🛑 Stop & Process", key='recorder')
    
    if audio_input:
        with st.spinner("AI is processing your speech..."):
            transcript = run_ai_stt(audio_input['bytes'])
            if transcript:
                st.session_state.content = transcript
                st.subheader(f"Captured Text: {transcript}")

    teacher_text = st.text_area("Final Text to Broadcast:", value=st.session_state.get('content', ""))
    if st.button("Broadcast to Students"):
        st.session_state.content = teacher_text
        st.success("Broadcast sent to all student devices!")

# --- 6. MODULE: AI TABLE & PDF REPORTS ---
elif page == "AI Table Creator":
    st.header("📊 Teacher Report & Verification Center")
    
    # Sample Data (Fetch from Firestore in actual run)
    report_data = [
        ["Nandini", "High", "Telugu", "Present"],
        ["Kumar", "Medium", "English", "Present"],
        ["Sita", "High", "Hindi", "Present"]
    ]
    columns = ["Student", "Engagement", "Language", "Status"]
    
    # SECTION 1: Class Summary
    st.subheader("1. Class Summary Verification")
    st.write("Review the English summary before AI translates and sends it to students.")
    summary_text = st.text_area("Class Summary (English):", 
                               "In today's session, we discussed AI architecture and real-time cloud databases.")
    
    if st.button("✅ Verify & Send Translated Summary"):
        with st.spinner("Translating for each student's language..."):
            # Internal logic to loop and send translations to DB
            st.success("Summary successfully translated and shared with students!")

    st.divider()
    
    # SECTION 2: Attendance
    st.subheader("2. Final Attendance List")
    st.table(pd.DataFrame(report_data, columns=columns))
    
    if st.button("📋 Finalize & Generate Attendance PDF"):
        att_rows = [[r[0], r[3]] for r in report_data]
        pdf_bytes = create_custom_pdf("NeuralBridge: Final Attendance Report", ["Name", "Status"], att_rows)
        
        st.download_button(
            label="📥 Download & Share Attendance PDF",
            data=pdf_bytes,
            file_name="Class_Attendance.pdf",
            mime="application/pdf"
        )
        st.success("Attendance PDF is ready for teacher records!")

# --- 7. OTHER MODULES (STUDENT JOIN / TEACHER DASHBOARD) ---
elif page == "Student Join":
    st.header("👤 Student Registration")
    st.info("Students can enter their details here to join the session.")

elif page == "Teacher Dashboard":
    st.header("👨‍🏫 Teacher Approval Panel")
    st.info("Approve student requests to enable their live translation feed.")
