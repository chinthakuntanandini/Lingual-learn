import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import google.cloud.exceptions

# --- 1. FIREBASE CONNECTION SETTINGS ---
@st.cache_resource
def init_connection():
    try:
        # Streamlit Secrets నుండి వివరాలను తీసుకుంటుంది
        firebase_info = st.secrets["firebase"]
        
        # Credentials తయారు చేయడం
        creds = service_account.Credentials.from_service_account_info(firebase_info)
        
        # Firestore క్లయింట్‌ని రిటర్న్ చేస్తుంది
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")
        return None

db = init_connection()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")

# Sidebar Navigation
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

st.title("🎓 NeuralBridge: Multi-Device AI Smart Class")

# --- 3. STUDENT JOIN PAGE ---
if page == "Student Join":
    st.header("Student Registration")
    name = st.text_input("Enter Your Name")
    roll = st.text_input("Enter Roll Number")
    lang = st.selectbox("Select Your Language", ["Telugu", "Hindi", "English", "Tamil"])

    if st.button("Register & Join"):
        if name and roll:
            try:
                # Firestore లో డేటా సేవ్ చేయడం (Line 42 issue fixed)
                db.collection("requests").document(roll).set({
                    "name": name,
                    "roll": roll,
                    "language": lang,
                    "status": "pending"
                })
                st.success(f"Hello {name}, your request sent to Teacher. Please wait for approval!")
            except Exception as e:
                st.error(f"Error saving data: {e}")
        else:
            st.warning("Please enter both Name and Roll Number")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("Teacher Approval Panel")
    
    try:
        # Pending రిక్వెస్ట్‌లను చూపించడం
        requests_ref = db.collection("requests").where("status", "==", "pending").stream()
        
        for doc in requests_ref:
            data = doc.to_dict()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{data['name']}** ({data['roll']}) - {data['language']}")
            with col2:
                if st.button("Approve", key=doc.id):
                    db.collection("requests").document(doc.id).update({"status": "approved"})
                    st.rerun()
    except Exception as e:
        st.error(f"Error fetching data: {e}")

# --- 5. LIVE CLASS PAGE ---
elif page == "Live Class":
    st.header("Live Interactive Session")
    st.write("Translation and Voice features will load here...")
    # ఇక్కడ మీ పాత Voice Recognition కోడ్ యాడ్ చేసుకోవచ్చు.
