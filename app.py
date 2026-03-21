import streamlit as st

# ---------------- DEMO DATA STORAGE ----------------
if "requests" not in st.session_state:
    st.session_state.requests = []

if "approved" not in st.session_state:
    st.session_state.approved = []

if "class_content" not in st.session_state:
    st.session_state.class_content = ""

# ---------------- UI SETTINGS ----------------
st.set_page_config(page_title="NeuralBridge AI", layout="wide")

page = st.sidebar.selectbox("Go to", ["Student Join", "Teacher Dashboard", "Live Class"])

st.title("🎓 NeuralBridge: Multi-Device AI Smart Class")

# ---------------- STUDENT JOIN ----------------
if page == "Student Join":
    st.header("Student Registration")

    name = st.text_input("Enter Your Name")
    roll = st.text_input("Enter Roll Number")
    lang = st.selectbox("Select Your Language", ["Telugu", "Hindi", "English", "Tamil"])

    if st.button("Register & Join"):
        if name and roll:
            student = {
                "name": name,
                "roll": roll,
                "language": lang,
                "status": "pending"
            }
            st.session_state.requests.append(student)
            st.success(f"{name}, your request sent to teacher! (Demo Mode)")
        else:
            st.warning("Please enter Name and Roll Number")

# ---------------- TEACHER DASHBOARD ----------------
elif page == "Teacher Dashboard":
    st.header("Teacher Approval Panel")

    if len(st.session_state.requests) == 0:
        st.info("No student requests yet")
    else:
        for i, req in enumerate(st.session_state.requests):
            col1, col2 = st.columns([3,1])

            with col1:
                st.write(f"{req['name']} ({req['roll']}) - {req['language']}")

            with col2:
                if st.button(f"Approve {req['roll']}", key=i):
                    st.session_state.approved.append(req)
                    st.session_state.requests.remove(req)
                    st.success(f"{req['name']} Approved!")

# ---------------- LIVE CLASS ----------------
elif page == "Live Class":
    st.header("Live Interactive Class")

    # Teacher input
    st.subheader("Teacher Panel")
    content = st.text_area("Enter Class Content")

    if st.button("Update Class"):
        st.session_state.class_content = content
        st.success("Class Updated!")

    # Student view
    st.subheader("Student View")

    if len(st.session_state.approved) == 0:
        st.warning("No students approved yet")
    else:
        for stu in st.session_state.approved:
            st.write(f"👨‍🎓 {stu['name']} ({stu['language']})")

        st.markdown("---")
        st.write("📚 Class Content:")
        st.write(st.session_state.class_content)
