import streamlit as st
import psycopg2
import ast
import bcrypt
import pickle
import json
import pandas as pd

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

# Password hashing function
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Verify hashed password
def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# Register user
def register_user(email, password):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    hashed_pw = hash_password(password)
    
    try:
        cur.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, %s)", (email, hashed_pw, 'user'))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error registering user: {e}")
        return False
    finally:
        conn.close()

# User authentication
def login_user(email, password):
    conn = get_db_connection()
    if not conn:
        return None

    cur = conn.cursor()
    cur.execute("SELECT password, role FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    conn.close()

    if user and check_password(password, user[0]):
        return user[1]  # Return role (user/admin)
    return None

# Profile Setup (Dashboard)
def dashboard(email, role):
    st.title("Profile Setup")

    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()

    cur.execute("SELECT full_name, skills, contact, locations, experience, job_role, salary, industries, job_type FROM users WHERE email = %s", (email,))
    user_data = cur.fetchone()

    full_name = user_data[0] if user_data and user_data[0] else ""
    skills = ast.literal_eval(user_data[1]) if user_data and user_data[1] else []
    contact = user_data[2] if user_data and user_data[2] else ""
    locations = ast.literal_eval(user_data[3]) if user_data and user_data[3] else []
    experience = user_data[4] if user_data and user_data[4] else 0
    job_role = user_data[5] if user_data and user_data[5] else ""
    salary = user_data[6] if user_data and user_data[6] else ""
    industries = ast.literal_eval(user_data[7]) if user_data and user_data[7] else []
    job_type = user_data[8] if user_data and user_data[8] else ""

    full_name = st.text_input("Full Name", full_name)
    skills = st.text_area("Skills (comma separated)", ", ".join(skills)).split(", ")
    contact = st.text_input("Contact Information", contact)
    locations = st.multiselect("Preferred Job Locations", ["Bangalore", "Hyderabad", "Delhi", "Mumbai", "Remote"], default=locations)
    experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=experience)
    job_role = st.text_input("Job Role", job_role)
    salary = st.text_input("Expected Salary Range", salary)
    industries = st.multiselect("Interested Industries", ["IT", "Finance", "Healthcare", "Education"], default=industries)
    job_type = st.selectbox("Preferred Job Type", ["Full-time", "Part-time", "Remote", "Contract"], index=["Full-time", "Part-time", "Remote", "Contract"].index(job_type) if job_type else 0)

    if st.button("Save Profile"):
        try:
            cur.execute("""
                UPDATE users SET full_name = %s, skills = %s, contact = %s, locations = %s, experience = %s, 
                job_role = %s, salary = %s, industries = %s, job_type = %s WHERE email = %s
            """, (full_name, json.dumps(skills), contact, json.dumps(locations), experience, job_role, salary, json.dumps(industries), job_type, email))
            conn.commit()
            st.success("Profile updated successfully!")
        except Exception as e:
            st.error(f"Error updating profile: {e}")

    conn.close()

# Job Recommendation Model
def get_job_recommendations(user_profile):
    try:
        with open('job_recommendation_model.pkl', 'rb') as model_file:
            model = pickle.load(model_file)

        user_df = pd.DataFrame([user_profile])

        recommendations = model.predict(user_df)
        return recommendations
    except Exception as e:
        st.error(f"Error generating job recommendations: {e}")
        return []

# Job Recommendation Button
if st.button("Get Job Recommendations"):
    user_profile = {
        'skills': skills,
        'experience': experience,
        'job_role': job_role,
        'industries': industries,
        'job_type': job_type
    }

    recommendations = get_job_recommendations(user_profile)

    st.write("### Job Recommendations:")
    for job in recommendations:
        st.write(f"- {job}")

