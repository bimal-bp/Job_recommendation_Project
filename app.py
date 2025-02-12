import streamlit as st
import psycopg2
import bcrypt
import ast  # To convert database array strings into Python lists

# Database connection
def get_db_connection():
    return psycopg2.connect(
        dbname="neondb",
        user="neondb_owner",
        password="npg_hnmkC3SAi7Lc",
        host="ep-steep-dawn-a87fu2ow-pooler.eastus2.azure.neon.tech",
        port="5432",
        sslmode="require"
    )

# Hash password
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Verify password
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Authenticate user
def authenticate_user(email, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password, role FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    conn.close()
    if user and check_password(password, user[0]):
        return user[1]  # Return role (user/admin)
    return None

# Fetch user profile
def get_user_profile(email):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE email = %s", (email,))
    user_profile = cur.fetchone()
    conn.close()
    return user_profile

# Save user profile
def save_user_profile(email, full_name, skills, contact, locations, experience, job_role, salary, industries, job_type):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if the profile exists
    cur.execute("SELECT email FROM user_profiles WHERE email = %s", (email,))
    if cur.fetchone():
        # Update existing profile
        cur.execute("""
            UPDATE user_profiles SET 
            full_name = %s, skills = %s, contact_number = %s, preferred_locations = %s, 
            experience = %s, job_role = %s, expected_salary = %s, industries = %s, job_type = %s 
            WHERE email = %s
        """, (full_name, skills, contact, locations, experience, job_role, salary, industries, job_type, email))
    else:
        # Insert new profile
        cur.execute("""
            INSERT INTO user_profiles (email, full_name, skills, contact_number, preferred_locations, 
            experience, job_role, expected_salary, industries, job_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (email, full_name, skills, contact, locations, experience, job_role, salary, industries, job_type))
    
    conn.commit()
    conn.close()

# Profile setup page
def profile_setup(email):
    st.subheader("Profile Setup")
    user_profile = get_user_profile(email)
    
    full_name = st.text_input("Full Name", value=user_profile[2] if user_profile else "")
    skills = st.text_area("Skills (comma-separated)", value=",".join(ast.literal_eval(user_profile[3])) if user_profile else "")
    contact = st.text_input("Contact Information", value=user_profile[4] if user_profile else "")
    locations = st.text_area("Preferred Job Locations (comma-separated)", value=",".join(ast.literal_eval(user_profile[5])) if user_profile else "")
    experience = st.number_input("Years of Experience", min_value=0, value=user_profile[6] if user_profile else 0)
    job_role = st.text_input("Job Role", value=user_profile[7] if user_profile else "")
    salary = st.text_input("Expected Salary Range", value=user_profile[8] if user_profile else "")
    industries = st.text_area("Interested Industries (comma-separated)", value=",".join(ast.literal_eval(user_profile[9])) if user_profile else "")
    job_type = st.text_input("Preferred Job Type (Full-time, Part-time, Remote, etc.)", value=user_profile[10] if user_profile else "")
    
    if st.button("Save Profile"):
        save_user_profile(email, full_name, skills.split(","), contact, locations.split(","), experience, job_role, salary, industries.split(","), job_type)
        st.success("Profile saved successfully!")

# Dashboard page
def dashboard(email, role):
    st.title("Dashboard")
    st.write(f"Welcome, {email}!")
    if role == "admin":
        st.subheader("Admin Panel")
        st.write("Manage users, upload market trends, and more.")
    else:
        st.subheader("User Dashboard")
        st.write("View job recommendations, saved profiles, and more.")
    
    if st.button("Edit Profile"):
        profile_setup(email)

# Main function
def main():
    st.title("User Authentication System")
    page = st.sidebar.selectbox("Choose Page", ["Login", "Sign Up", "Dashboard"])
    
    if page == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            role = authenticate_user(email, password)
            if role:
                st.success("Login Successful!")
                dashboard(email, role)
            else:
                st.error("Invalid credentials. Please try again.")
    
    elif page == "Sign Up":
        new_email = st.text_input("New Email")
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            hashed_password = hash_password(new_password)
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, 'user')", (new_email, hashed_password))
                conn.commit()
                st.success("Account created successfully! You can now log in.")
            except psycopg2.errors.UniqueViolation:
                st.error("Email already exists. Please use a different email.")
            conn.close()
    
    elif page == "Dashboard":
        st.warning("Please log in first!")

if __name__ == "__main__":
    main()
