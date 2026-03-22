import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from streamlit_mic_recorder import mic_recorder

# --- 1. SECURE DATABASE CONNECTION ---
@st.cache_resource
def init_db():
    """
    Connects to Google Cloud Firestore and handles RSA key formatting.
    Professional English Comment: This ensures real-time sync between Teacher and Student.
    """
    try:
        if "firebase" in st.secrets:
            info = dict(st.secrets["firebase"])
            # Fixing Private Key formatting
            info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
    return None

db = init_db()

# --- 2. UI NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
st.sidebar.caption("Real-time Multilingual Sync")
mode = st.sidebar.radio("Navigation:", ["Student Portal", "Teacher Control"])

# --- 3. STUDENT PORTAL ---
if mode == "Student Portal":
    st.header("👤 Student Portal")
    
    # Section A: Attendance Sync
    st.subheader("📋 Mark Attendance")
    name = st.text_input("Full Name")
    roll = st.text_input("Roll Number")
    
    if st.button("Submit Attendance"):
        if db and name and roll:
            db.collection("attendance").document(roll).set({
                "Name": name, "Roll": roll, "Status": "Present",
                "Timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success("Attendance Synced!")

    st.divider()

    # Section B: Live Class Notes (Teacher updates this)
    st.subheader("📖 Live Class Notes")
    if db:
        # Fetching the latest lecture notes from the cloud
        lecture_ref = db.collection("lectures").document("current_session").get()
        if lecture_ref.exists:
            notes = lecture_ref.to_dict().get("content", "Waiting for teacher to start...")
            st.info(notes) # ఇక్కడ స్టూడెంట్‌కి టీచర్ నోట్స్ కనిపిస్తాయి
        else:
            st.write("No active lecture notes found.")

# --- 4. TEACHER CONTROL ---
elif mode == "Teacher Control":
    st.header("🎙️ Teacher Dashboard")
    
    # Attendance Tracker
    st.subheader("📋 Live Attendance")
    if db:
        docs = db.collection("attendance").stream()
        attendance_list = [doc.to_dict() for doc in docs]
        if attendance_list:
            st.table(pd.DataFrame(attendance_list)[['Name', 'Roll']])
    
    st.divider()

    # AI Recording & Transcription
    st.subheader("🎙️ AI Lecture Capture")
    st.write("Click below to record your lecture:")
    
    # Recording Logic
    audio = mic_recorder(start_prompt="▶️ Start Recording", stop_prompt="🛑 Stop & Sync", key='teacher_mic')
    
    if audio:
        # Mocking the AI Transcription for the M.Tech Demo
        transcription = "AI Transcription: Today we are discussing Cloud Data Sync in AIML projects."
        st.session_state.lecture_content = transcription
        
        # Saving notes to Firestore so Students can see them
        if db:
            db.collection("lectures").document("current_session").set({
                "content": transcription,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success("Lecture synced to Student Portal!")

    # Editable area for Teacher
    final_notes = st.text_area("Final Summary to Students:", value=st.session_state.get('lecture_content', ""))
    if st.button("Update Students"):
         if db:
            db.collection("lectures").document("current_session").update({"content": final_notes})
            st.success("Notes Updated for Students!")
