import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account

# --- 1. FIREBASE CONNECTION SETTINGS ---
# Using cache_resource to keep the connection alive and prevent reloading
@st.cache_resource
def init_connection():
    try:
        # Checking if firebase section exists in Streamlit Secrets
        if "firebase" not in st.secrets:
            st.error("Firebase section not found in Streamlit Secrets!")
            return None
            
        firebase_info = st.secrets["firebase"]
        
        # FIXING THE PEM FILE ERROR:
        # Replacing escaped newlines with actual newline characters
        raw_key = firebase_info["private_key"]
        private_key = raw_key.replace("\\n", "\n")
        
        # Cleaning the private key to remove any extra spaces or quotes
        if "-----BEGIN PRIVATE KEY-----" in private_key:
            private_key = private_key.strip()

        # Building the credentials dictionary for Firebase
        creds_dict = {
            "type": firebase_info["type"],
            "project_id": firebase_info["project_id"],
            "private_key_id": firebase_info["private_key_id"],
            "private_key": private_key,
            "client_email": firebase_info["client_email"],
            "client_id": firebase_info["client_id"],
            "auth_uri": firebase_info["auth_uri"],
            "token_uri": firebase_info["token_uri"],
            "auth_provider_x509_cert_url": firebase_info["auth_provider_x509_cert_url"],
            "client_x509_cert_url": firebase_info["client_x509_cert_url"],
        }
        
        # Authenticating with Google Cloud
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=firebase_info["project_id"])
        
    except Exception as e:
        # Displaying the specific connection error on the app screen
        st.error(f"Firebase Connection Error: {e}")
        return None

# Initializing the database object
db = init_connection()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="NeuralBridge AI", layout="wide")

# Sidebar for navigation between different pages
page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

st.title("🎓 NeuralBridge: Multi-Device AI Smart Class")

# --- 3. STUDENT JOIN PAGE ---
if page == "Student Join":
    st.header("Student Registration")
    name = st.text_input("Enter Your Name")
    roll = st.text_input("Enter Roll Number")
    lang = st.selectbox("Select Your Language", ["Telugu", "Hindi", "English", "Tamil"])

    if st.button("Register & Join"):
        if db is None:
            st.error("Database connection failed. Please check your Secrets configuration.")
        elif name and roll:
            try:
                # Saving student details to Firestore 'requests' collection
                db.collection("requests").document(roll).set({
                    "name": name,
                    "roll": roll,
                    "language": lang,
                    "status": "pending"
                })
                st.success(f"Hello {name}, your request has been sent to the Teacher. Please wait for approval!")
            except Exception as e:
                st.error(f"Error while saving data: {e}")
        else:
            st.warning("Please enter both Name and Roll Number.")

# --- 4. TEACHER DASHBOARD ---
elif page == "Teacher Dashboard":
    st.header("Teacher Approval Panel")
    
    if db is None:
        st.error("Database connection is not active.")
    else:
        try:
            # Fetching only the students with 'pending' status
            requests_ref = db.collection("requests").where("status", "==", "pending").stream()
            
            found = False
            for doc in requests_ref:
                found = True
                data = doc.to_dict()
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{data['name']}** ({data['roll']}) - Language: {data['language']}")
                with col2:
                    if st.button("Approve", key=doc.id):
                        # Updating the status to 'approved' in Firestore
                        db.collection("requests").document(doc.id).update({"status": "approved"})
                        st.rerun()
            
            if not found:
                st.info("No pending requests found.")
                
        except Exception as e:
            st.error(f"Error while fetching data: {e}")

# --- 5. LIVE CLASS PAGE ---
elif page == "Live Class":
    st.header("Live Interactive Session")
    st.write("Voice recognition and translation features will load here...")
    # Add your translation logic here in future updates
