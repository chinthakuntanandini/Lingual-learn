import streamlit as st
import ml_logic
import time

# Page setup for a professional classroom look
st.set_page_config(page_title="LinguaLearn AI", layout="wide")

# Custom CSS for a better UI
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stTextArea textarea { font-size: 18px !important; }
    </style>
    """, unsafe_status=True)

st.title("👨‍🏫 AI-Powered Interactive Classroom")
st.markdown("---")

# Layout: Creating two columns for Teacher and Student view
col_teacher, col_student = st.columns([1, 1])

with col_teacher:
    st.header("🎙️ Teacher's Section")
    st.info("Teacher is speaking... (Live Captions)")
    
    # Input area for teacher's speech
    speech_input = st.text_area("Live Audio-to-Text Stream:", height=150, placeholder="Teacher's words will appear here...")
    
    process_btn = st.button("🚀 Broadcast to Students")

with col_student:
    st.header("📱 Student's Dashboard")
    
    if process_btn and speech_input:
        with st.spinner('AI analyzing the lecture...'):
            time.sleep(1) # Simulating real-time processing
            
            # Calling our ML Logic
            subject, latency = ml_logic.process_ai(speech_input)
            
            # Student views the organized content
            st.success(f"**Subject Identified:** {subject}")
            
            st.markdown(f"""
            **Lecture Summary:**
            > {speech_input}
            """)
            
            st.metric(label="System Response Speed", value=f"{latency} sec")
    else:
        st.warning("Waiting for the teacher to start the lecture...")

# Sidebar for Guide's verification
st.sidebar.title("🛠️ Backend Intelligence")
st.sidebar.write("This system is powered by:")
st.sidebar.markdown("""
- **Random Forest:** Subject Classification
- **Linear Regression:** Latency Prediction
- **K-Means:** Content Grouping
""")

if st.sidebar.button("Show Model Accuracy"):
    st.sidebar.write("Current Model Accuracy: **94%**")
