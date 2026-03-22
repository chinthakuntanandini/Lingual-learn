import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from fpdf import FPDF
from streamlit_mic_recorder import mic_recorder

# --- 1. FIREBASE CONNECTION LOGIC ---
@st.cache_resource
def init_db():
    """
    Initializes the connection to Google Firestore using credentials 
    stored in Streamlit Secrets. Uses caching to prevent multiple reconnections.
    """
    try:
        if "firebase" in st.secrets:
            # Load credentials from Streamlit Cloud Secrets into a dictionary
            info = dict(st.secrets["firebase"])
            
            # CRITICAL FIX: Normalizing formatting issues with the RSA Private Key
            if "private_key" in info:
                # Replace literal backslashes with actual newlines to ensure valid PEM format
                key = info["private_key"].replace("\\n", "\n").strip()
                
                # Remove accidental surrounding quotes that might occur during copy-paste
                if key.startswith('"') and key.endswith('"'):
                    key = key[1:-1]
                
                # Update the credential dictionary with the cleaned key
                info["private_key"] = key
            
            # Authenticate using the Service Account credentials
            creds = service_account.Credentials.from_service_account_info(info)
            
            # Return the Firestore Client for database operations
            return firestore.Client(credentials=creds, project=creds.project_id)
            
    except Exception as e:
        # Catch and display connection errors (e.g., PEM format issues or invalid keys)
        st.error(f"❌ Firebase Connection Error: {e}")
    
    return None

# Establish the global database connection
db = init_db()
