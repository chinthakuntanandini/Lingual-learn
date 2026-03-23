import streamlit as st
import pandas as pd
from google.cloud import firestore
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from fpdf import FPDF
import io

# --- 1. FIREBASE CONNECTION ---
@st.cache_resource
def init_db():
    try:
        info = dict(st.secrets["firebase"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        st.error(f"Cloud Connection Error: {e}")
    return None

db = init_db()

# --- 2. PDF GENERATION ENGINE (Standard English) ---
def create_english_pdf(title, content_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    
    for line in content_list:
        pdf.multi_cell(0, 10, txt=str(line))
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
choice = st.sidebar.radio("Navigation", ["Student Portal", "Teacher Dashboard"])

# --- 4. TEACHER DASHBOARD ---
if choice == "Teacher Dashboard":
    st.header("🎙️ Teacher Command Center")
    
    # Lecture Recording
    st.subheader("🔊 Live Lecture Capture")
    audio = mic_recorder(start_prompt="▶️ Start Recording", stop_prompt="🛑 Stop & Process")
    
    if audio:
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio['bytes'])) as source:
            text = recognizer.recognize_google(recognizer.record(source))
            st.session_state.master_notes = text
            # Sync text to Cloud
            db.collection("session").document("live").set({"notes": text})
            st.success("Lecture synced to Cloud!")

    st.text_area("Current Lecture Content:", value=st.session_state.get('master_notes', ""), height=150)

    st.divider()

    # Final PDF Controls
    st.subheader("📤 Post-Class Distribution")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📢 Publish Class Notes PDF"):
            content = st.session_state.get('master_notes', "No content recorded.")
            pdf_data = create_english_pdf("Official Class Notes", [content])
            # Upload to Cloud indicator
            db.collection("delivery").document("notes").set({"ready": True, "data": content})
            st.success("Notes PDF is now available for Students!")

    with col2:
        if st.button("📝 Publish Attendance PDF"):
            docs = db.collection("attendance").stream()
            names = [f"{d.to_dict()['Name']} - Roll: {d.to_dict()['Roll']}" for d in docs]
            if names:
                db.collection("delivery").document("attendance").set({"ready": True, "list": names})
                st.success("Attendance PDF is now available for Students!")
            else:
                st.warning("No attendance records found.")

# --- 5. STUDENT PORTAL ---
elif choice == "Student Portal":
    st.header("👤 Student Portal")
    
    if 'verified' not in st.session_state:
        with st.form("Login"):
            s_name = st.text_input("Full Name")
            s_roll = st.text_input("Roll Number")
            if st.form_submit_button("Join Class"):
                db.collection("attendance").document(s_roll).set({"Name": s_name, "Roll": s_roll})
                st.session_state.verified = True
                st.rerun()
    else:
        st.success(f"Verified: {st.session_state.get('s_name', 'Student')}")
        
        # Display Live Text (if any)
        live_ref = db.collection("session").document("live").get()
        if live_ref.exists:
            st.info(f"**Live Notes:** {live_ref.to_dict()['notes']}")

        st.divider()
        st.subheader("📂 Download Official Documents")

        # Download Notes PDF
        notes_ref = db.collection("delivery").document("notes").get()
        if notes_ref.exists and notes_ref.to_dict().get("ready"):
            notes_content = [notes_ref.to_dict()['data']]
            pdf_file = create_english_pdf("Class Notes", notes_content)
            st.download_button("📥 Download Class Notes (PDF)", data=pdf_file, file_name="Class_Notes.pdf")

        # Download Attendance PDF
        att_ref = db.collection("delivery").document("attendance").get()
        if att_ref.exists and att_ref.to_dict().get("ready"):
            att_list = att_ref.to_dict()['list']
            pdf_file = create_english_pdf("Class Attendance Sheet", att_list)
            st.download_button("📥 Download Attendance Sheet (PDF)", data=pdf_file, file_name="Attendance_List.pdf")
