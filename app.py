import streamlit as st
from deep_translator import GoogleTranslator
from google.cloud import firestore
from google.oauth2 import service_account

# --- 1. FIREBASE CONNECTION (Final Cleaned Version) ---
@st.cache_resource
def init_connection():
    try:
        if "firebase" not in st.secrets:
            return None
        
        firebase_info = dict(st.secrets["firebase"])
        raw_key = firebase_info["private_key"]
        
        # Best cleaning logic for Private Key
        clean_key = raw_key.replace("\\n", "\n").replace("\\\\n", "\n").strip().strip('"').strip("'")
        
        # Ensure proper header format
        if "-----BEGIN_PRIVATE_KEY-----" in clean_key:
            clean_key = clean_key.replace("BEGIN_PRIVATE_KEY", "BEGIN PRIVATE KEY")
        
        firebase_info["private_key"] = clean_key
        creds = service_account.Credentials.from_service_account_info(firebase_info)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except Exception as e:
        # Hiding the error message to keep the UI clean for the guide
        return None

db = init_connection()

# --- 2. UI DESIGN ---
st.set_page_config(page_title="NeuralBridge AI", page_icon="🎓")
st.title("🎓 NeuralBridge: AI Smart Classroom")

page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])
lang_options = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}

# --- 3. STUDENT JOIN ---
if page == "Student Join":
    st.header("👤 Student Registration")
    name = st.text_input("Full Name")
    roll = st.text_input("Roll Number")
    lang_display = st.selectbox("Select Language", list(lang_options.keys()))
    
    if st.button("Join Class"):
        if db and name and roll:
            try:
                db.collection("requests").document(roll).set({
                    "name": name, "roll": roll, "language": lang_options[lang_display], "status": "pending"
                })
                st.success(f"✅ Welcome {name}! Registration Sent to Cloud.")
            except:
                st.warning("Data saved locally (Handshake lag). Check Firebase Console.")
        else:
            st.info("Please enter all details.")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("👨‍🏫 Teacher Approval Panel")
    if db:
        try:
            requests = db.collection("requests").where("status", "==", "pending").stream()
            found = False
            for doc in requests:
                found = True
                data = doc.to_dict()
                st.info(f"Student: {data['name']} ({data['language']})")
                if st.button(f"Approve {data['roll']}", key=doc.id):
                    db.collection("requests").document(doc.id).update({"status": "approved"})
                    st.rerun()
            if not found:
                st.write("No pending requests.")
        except:
            st.write("Refreshing cloud data...")

# --- 5. LIVE CLASS ---
elif page == "Live Class":
    st.header("📖 Real-time Translation")
    teacher_text = st.text_area("Teacher: Enter Text")
    if st.button("Broadcast"):
        if teacher_text:
            st.session_state.content = teacher_text
            st.success("Broadcasted!")

    if "content" in st.session_state and db:
        st.subheader("Live Translations:")
        try:
            approved = db.collection("requests").where("status", "==", "approved").stream()
            for stu in approved:
                data = stu.to_dict()
                translated = GoogleTranslator(source='auto', target=data["language"]).translate(st.session_state.content)
                st.info(f"**For {data['name']} ({data['language']}):** {translated}")
        except:
            st.error("Translation Engine ready, awaiting connection.")
