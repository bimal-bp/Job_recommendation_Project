import streamlit as st
import psycopg2
import ast  # To convert database array strings into Python lists

# Hardcoded dictionary for skill learning links
skill_links = {
    "Blockchain": "https://www.coursera.org/specializations/blockchain",
    "IoT": "https://www.udemy.com/course/iot-internet-of-things/",
    "5G": "https://www.coursera.org/learn/5g-wireless",
    "Augmented Reality (AR) & Virtual Reality (VR)": "https://www.udemy.com/course/ar-vr-development/",
    "AI, ML, and Data Science": "https://www.deeplearning.ai/courses/",
    "Cloud Computing": "https://www.udemy.com/course/aws-certified-cloud-practitioner/",
    "Generative AI": "https://www.coursera.org/specializations/generative-ai",
}

# Database connection
def get_db_connection():
    try:
        return psycopg2.connect(
            dbname="neondb",
            user="neondb_owner",
            password="npg_hnmkC3SAi7Lc",
            host="ep-steep-dawn-a87fu2ow-pooler.eastus2.azure.neon.tech",
            port="5432",
            sslmode="require"
        )
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# Function to safely parse database string values
def safe_parse(value, default=[]):
    try:
        return ast.literal_eval(value) if value else default
    except (ValueError, SyntaxError):
        return default

# Fetch user skills from the database
def get_user_skills(email):
    conn = get_db_connection()
    if not conn:
        return []
    
    cur = conn.cursor()
    cur.execute("SELECT skills FROM users WHERE email = %s", (email,))
    user_data = cur.fetchone()
    conn.close()

    return safe_parse(user_data[0]) if user_data else []

# Fetch market trend skills
def get_market_trend_skills():
    conn = get_db_connection()
    if not conn:
        return []
    
    cur = conn.cursor()
    cur.execute("SELECT trend FROM market_trends")  # Assuming trends contain skills
    trends = cur.fetchall()
    conn.close()

    return [trend[0] for trend in trends] if trends else []

# Market Trends Page
def market_trends_page(email):
    st.title("Market Trends")

    # Fetch and display market trends
    market_trend_skills = get_market_trend_skills()

    if market_trend_skills:
        st.write("### Trending Skills in the Market:")
        for skill in market_trend_skills:
            st.write(f"- {skill}")
    else:
        st.write("No market trends available.")

    # Fetch user skills
    user_skills = get_user_skills(email)

    # Compare user skills with trending skills
    missing_skills = list(set(market_trend_skills) - set(user_skills))

    if missing_skills:
        st.write("### Recommended Skills to Learn:")
        for skill in missing_skills[:2]:  # Show only 2 missing skills
            link = skill_links.get(skill, "#")
            st.markdown(f"- [{skill}]({link})", unsafe_allow_html=True)
    else:
        st.write("You're up to date with the trending skills! 🎉")

# Profile Setup (Dashboard Page)
def dashboard(email, role):
    st.subheader("Profile Setup")

    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()

    # Fetch existing user data
    cur.execute("SELECT full_name, skills, contact, locations, experience, job_role, salary, industries, job_type FROM users WHERE email = %s", (email,))
    user_data = cur.fetchone()

    # Default values if no data exists
    full_name = user_data[0] if user_data and user_data[0] else ""
    skills = safe_parse(user_data[1])
    contact = user_data[2] if user_data and user_data[2] else ""
    locations = safe_parse(user_data[3])
    experience = user_data[4] if user_data and user_data[4] else 0
    job_role = user_data[5] if user_data and user_data[5] else ""
    salary = user_data[6] if user_data and user_data[6] else ""
    industries = safe_parse(user_data[7])
    job_type = user_data[8] if user_data and user_data[8] else ""

    # Input fields
    full_name = st.text_input("Full Name", full_name)
    skills = st.text_area("Skills (comma separated)", ", ".join(skills)).split(", ")
    contact = st.text_input("Contact Information", contact)
    locations = st.multiselect("Preferred Job Locations", ["Bangalore", "Hyderabad", "Delhi", "Mumbai", "Remote"], default=locations)
    experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=experience)
    job_role = st.text_input("Job Role", job_role)
    salary = st.text_input("Expected Salary Range", salary)
    industries = st.multiselect("Interested Industries", ["IT", "Finance", "Healthcare", "Education"], default=industries)
    job_type = st.selectbox("Preferred Job Type", ["Full-time", "Part-time", "Remote", "Contract"], index=["Full-time", "Part-time", "Remote", "Contract"].index(job_type) if job_type else 0)

    # Save button
    if st.button("Save Profile"):
        try:
            cur.execute("""
                UPDATE users SET full_name = %s, skills = %s, contact = %s, locations = %s, experience = %s, 
                job_role = %s, salary = %s, industries = %s, job_type = %s WHERE email = %s
            """, (full_name, skills, contact, locations, experience, job_role, salary, industries, job_type, email))
            conn.commit()
            st.success("Profile updated successfully!")
        except Exception as e:
            st.error(f"Error updating profile: {e}")

    conn.close()

# Authentication Page
def authentication_page():
    option = st.radio("Select Option", ["Login", "Sign Up", "Admin Login"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if option == "Login":
        if st.button("Login"):
            role = authenticate_user(email, password)
            if role:
                st.success("Login Successful!")
                st.session_state["logged_in"] = True
                st.session_state["email"] = email
                st.session_state["role"] = role
                st.rerun()
            else:
                st.error("Invalid email or password.")

    elif option == "Sign Up":
        if st.button("Sign Up"):
            if register_user(email, password):
                st.success("Registration Successful! Please login.")
            else:
                st.error("Registration failed. Please try again.")

# Main Function
def main():
    st.title("User Authentication System")

    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["email"] = None
        st.session_state["role"] = None

    if st.session_state["logged_in"]:
        menu_options = ["Profile Setup", "Market Trends"]
        choice = st.sidebar.radio("Go to", menu_options)

        if choice == "Profile Setup":
            dashboard(st.session_state["email"], st.session_state["role"])
        elif choice == "Market Trends":
            market_trends_page(st.session_state["email"])
    else:
        authentication_page()

if __name__ == "__main__":
    main()
