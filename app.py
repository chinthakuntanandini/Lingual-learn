import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF
from googletrans import Translator
import datetime
import os

# --- 1. FIREBASE CONNECTION ---
# GitHub లో మీరు అప్‌లోడ్ చేసిన key.json ని ఇది వాడుకుంటుంది
if not firebase_admin._apps:
    try:
        if os.path.exists("key.json"):
            cred = credentials.Certificate("key.json")
            firebase_admin.initialize_app(cred)
        else:
            st.error("Error: key.json file is missing in GitHub! Please upload it.")
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")

db = firestore.client()
translator = Translator()

# --- 2. NAVIGATION ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")
st.title("🎓 NeuralBridge: Multi-Device AI Smart Class")
sidebar = st.sidebar.radio("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

# --- 3. STUDENT JOIN (Phone 1) ---
if sidebar == "Student Join":
    st.header("Student Registration")
    name = st.text_input("Enter Your Name")
    roll = st.text_input("Enter Roll Number")
    
    # భాషల ఎంపిక (Language Selection)
    lang_options = {"Telugu": "te", "Hindi": "hi", "Tamil": "ta", "English": "en", "Kannada": "kn"}
    selected_lang = st.selectbox("Select Your Language", list(lang_options.keys()))
    
    if st.button("Send Request to Teacher"):
        if name and roll:
            # Firestore లో డేటా సేవ్ - ఇది వేరే ఫోన్ కి కనిపిస్తుంది
            db.collection("requests").document(roll).set({
                "name": name,
                "roll_no": roll,
                "language": selected_lang,
                "lang_code": lang_options[selected_lang],
                "status": "pending",
                "time": datetime.datetime.now()
            })
            st.success(f"Hi {name}, your request sent! Please wait for Teacher's approval.")
        else:
            st.error("Please enter both Name and Roll Number.")

# --- 4. TEACHER DASHBOARD (Phone 2) ---
elif sidebar == "Teacher Dashboard":
    st.header("Teacher Approval Panel")
    
    # Database నుండి 'pending' రిక్వెస్ట్స్ ని తీసుకుంటున్నాం
    requests = db.collection("requests").where("status", "==", "pending").stream()
    
    found = False
    for req in requests:
        found = True
        data = req.to_dict()
        col1, col2 = st.columns([3, 1])
        col1.write(f"🔔 **{data['name']}** (ID: {data['roll_no']}) wants to join | Lang: {data['language']}")
        
        if col2.button(f"Accept {data['name']}", key=data['roll_no']):
            db.collection("requests").document(data['roll_no']).update({"status": "accepted"})
            st.success(f"Accepted {data['name']}!")
            st.rerun()
            
    if not found:
        st.info("No new requests. Waiting for students to join...")

# --- 5. LIVE CLASS (Real-time Broadcast & Translation) ---
elif sidebar == "Live Class":
    st.header("Live Interactive Session")
    
    # TEACHER SECTION
    st.subheader("👨‍🏫 Teacher Section")
    lesson_text = st.text_area("Type your lesson here (in English):")
    
    if st.button("Broadcast Lesson"):
        if lesson_text:
            # పాఠాన్ని Firebase లో సేవ్ చేస్తున్నాం
            db.collection("class_content").document("current_lesson").set({
                "text": lesson_text,
                "timestamp": datetime.datetime.now()
            })
            st.success("Lesson broadcasted to all students!")
        else:
            st.warning("Please type a lesson before broadcasting.")

    st.divider()

    # STUDENT SECTION
    st.subheader("📖 Student Section (Auto-Translation)")
    student_id = st.text_input("Enter your Roll No to see lesson in your language:")
    
    if student_id:
        # విద్యార్థి అప్రూవ్ అయ్యారో లేదో చెక్ చేస్తున్నాం
        student_ref = db.collection("requests").document(student_id).get()
        if student_ref.exists and student_ref.to_dict()['status'] == "accepted":
            s_data = student_ref.to_dict()
            
            # Firebase నుండి టీచర్ పంపిన పాఠాన్ని తీసుకుంటున్నాం
            lesson_ref = db.collection("class_content").document("current_lesson").get()
            if lesson_ref.exists:
                original_msg = lesson_ref.to_dict()['text']
                
                # విద్యార్థి ఎంచుకున్న భాషలోకి అనువాదం
                translated_msg = translator.translate(original_msg, dest=s_data['lang_code']).text
                
                st.info(f"Welcome {s_data['name']}! Here is the lesson in **{s_data['language']}**:")
                st.success(translated_msg)
            else:
                st.info("Waiting for teacher to start the lesson...")
        else:
            st.error("Your ID is not recognized or not yet accepted by the teacher.")
