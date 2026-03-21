import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF
from googletrans import Translator
import datetime
import json

# --- 1. FIREBASE SETUP ---
# Streamlit Secrets ద్వారా కనెక్ట్ చేయడం సురక్షితం మరియు సులభం
if not firebase_admin._apps:
    try:
        # GitHub లో key.json అప్‌లోడ్ చేసి ఉంటే ఇది పనిచేస్తుంది
        cred = credentials.Certificate("key.json")
        firebase_admin.initialize_app(cred)
    except:
        st.error("Please upload key.json to GitHub or check Firebase Rules.")

db = firestore.client()
translator = Translator()

# --- 2. UI & NAVIGATION ---
st.title("🎓 NeuralBridge: Multi-Device Class")
sidebar = st.sidebar.radio("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

# --- 3. STUDENT JOIN (Phone 1) ---
if sidebar == "Student Join":
    st.header("Student Registration")
    name = st.text_input("Name")
    roll = st.text_input("Roll No")
    lang = st.selectbox("Language", ["Telugu", "Hindi", "Tamil", "English"])
    
    if st.button("Send Request"):
        if name and roll:
            # Firestore లో సేవ్ చేస్తున్నాం - ఇది వేరే ఫోన్ కి కనిపిస్తుంది
            db.collection("requests").document(roll).set({
                "name": name,
                "roll_no": roll,
                "language": lang,
                "status": "pending"
            })
            st.success("Request sent to Teacher's phone!")
        else:
            st.error("Fill all details")

# --- 4. TEACHER DASHBOARD (Phone 2) ---
elif sidebar == "Teacher Dashboard":
    st.header("Teacher Dashboard")
    
    # Database నుండి లైవ్ రిక్వెస్ట్స్ తీసుకుంటున్నాం
    requests = db.collection("requests").where("status", "==", "pending").stream()
    
    found = False
    for req in requests:
        found = True
        data = req.to_dict()
        st.write(f"🔔 **{data['name']}** (Roll: {data['roll_no']}) wants to join.")
        if st.button(f"Accept {data['name']}", key=data['roll_no']):
            db.collection("requests").document(data['roll_no']).update({"status": "accepted"})
            st.success(f"Accepted {data['name']}!")
            st.rerun()
            
    if not found:
        st.info("Waiting for student requests...")

# --- 5. LIVE CLASS ---
elif sidebar == "Live Class":
    st.header("Live Class Control")
    msg = st.text_area("Type lesson in English")
    if st.button("Broadcast to Students"):
        st.session_state['last_msg'] = msg
        st.success("Lesson broadcasted to all accepted students!")
