import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from fpdf import FPDF

# --- 1. FIREBASE CONNECTION ---
@st.cache_resource
def init_db():
    if "firebase" in st.secrets:
        info = dict(st.secrets["firebase"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(credentials=creds, project=creds.project_id)
    return None

db = init_db()

# --- 2. SIDEBAR NAVIGATION ---
st.sidebar.title("🎓 NeuralBridge AI")
user_role = st.sidebar.radio("Select Your Role:", ["Student", "Teacher"])

# --- 3. STUDENT MODULE (Writing to Database) ---
if user_role == "Student":
    st.header("👤 Student Portal")
    s_name = st.text_input("Name")
    s_roll = st.text_input("Roll No")
    
    if st.button("Join Class"):
        if db and s_name and s_roll:
            # Firestore లో 'attendance' అనే కలెక్షన్ లో డేటా సేవ్ అవుతుంది
            db.collection("attendance").document(s_roll).set({
                "Name": s_name,
                "Roll": s_roll,
                "Status": "Present"
            })
            st.success(f"Done! {s_name}, your attendance is sent to Teacher.")
        else:
            st.error("Please fill details or check Database connection.")

# --- 4. TEACHER MODULE (Reading from Database) ---
elif user_role == "Teacher":
    st.header("🎙️ Teacher Control Room")
    st.subheader("📋 Live Attendance Tracker")
    
    if db:
        # Database నుంచి లైవ్ గా డేటా తెచ్చుకుంటుంది
        docs = db.collection("attendance").stream()
        attendance_data = [doc.to_dict() for doc in docs]
        
        if attendance_data:
            df = pd.DataFrame(attendance_data)
            st.table(df) # ఇక్కడ స్టూడెంట్ పంపిన డేటా కనిపిస్తుంది
        else:
            st.info("Waiting for students to join...")
    
    if st.button("Refresh Attendance"):
        st.rerun() # కొత్త డేటా కోసం రిఫ్రెష్ బటన్

    st.divider()
    st.subheader("📥 Final Reports")
    # (PDF generation logic follows...)
