import streamlit as st
from deep_translator import GoogleTranslator
from google.cloud import firestore
from google.oauth2 import service_account
import pandas as pd

# --- 1. FIREBASE CONNECTION (Using Secrets) ---
@st.cache_resource
def init_connection():
    try:
        if "firebase" not in st.secrets:
            st.error("Firebase secrets not found! Check Streamlit Settings.")
            return None
            
        firebase_info = dict(st.secrets["firebase"])
        # Handling the private key formatting
        raw_key = firebase_info["private_key"]
        private_key = raw_key.replace("\\n", "\n").strip().strip('"')
        firebase_info["private_key"] = private_key

        creds = service_account.Credentials.from_service_account_info(firebase_info)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except Exception as e:
        st.error(f"Firebase Error: {e}")
        return None

db = init_connection()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="NeuralBridge AI", page_icon="🎓", layout="wide")
st.title("🎓 NeuralBridge: AI Smart Classroom")
st.markdown("---")

# Navigation Sidebar
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

# Language Options
lang_options = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Urdu": "ur"}
lang_map = {v: k for k, v in lang_options.items()}

# --- 3. STUDENT JOIN PAGE ---
if page == "Student Join":
    st.header("👤 Student Registration")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name")
        roll = st.text_input("Roll Number / ID")
    with col2:
        lang_display = st.selectbox("Select Your Native Language", list(lang_options.keys()))
        lang_code = lang_options[lang_display]

    if st.button("Join Class"):
        if db and name and roll:
            db.collection("requests").document(roll).set({
                "name": name,
                "roll": roll,
                "language": lang_code,
                "status": "pending"
            })
            st.success(f"Registration Successful! {name}, wait for teacher's approval.")
        else:
            st.warning("Please fill all details and check Firebase connection.")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("👨‍🏫 Teacher Approval Panel")
    if db:
        requests = db.collection("requests").where("status", "==", "pending").stream()
        found = False
        for doc in requests:
            found = True
            data = doc.to_dict()
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.info(f"**Student:** {data['name']} | **ID:** {data['roll']} | **Language:** {lang_map.get(data['language'])}")
            with col_b:
                if st.button("Approve", key=doc.id):
                    db.collection("requests").document(doc.id).update({"status": "approved"})
                    st.rerun()
        if not found:
            st.write("No pending requests.")

# --- 5. LIVE CLASS PAGE ---
elif page == "Live Class":
    st.header("📖 Real-time Translation Session")
    
    # Teacher Input: Text based for quick submission
    teacher_text = st.text_area("Teacher: Enter Lesson Text here", height=150)
    
    if st.button("Broadcast to Students"):
        if teacher_text:
            st.session_state.class_content = teacher_text
            st.success("Lesson Content Shared!")
        else:
            st.warning("Please enter some text.")

    st.markdown("---")
    
    # Processing for Approved Students
    if "class_content" in st.session_state:
        st.subheader("Translated Content for Students")
        if db:
            approved = db.collection("requests").where("status", "==",
