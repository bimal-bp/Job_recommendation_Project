import streamlit as st
import psycopg2
import bcrypt
import ast  # To convert database array strings into Python lists
import pickle  # For loading the job recommendation model
import numpy as np

# Load the job recommendation model
with open("job_recommendation_system.pkl", "rb") as model_file:
    job_model = pickle.load(model_file)

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

# Hash password
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Verify password
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Authenticate user
def authenticate_user(email, password):
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

# Save new user
def register_user(email, password):
    conn = get_db_connection()
    if not conn:
        return False
    
    cur = conn.cursor()
    try:
        hashed_password = hash_password(password)
        cur.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, 'user')", (email, hashed_password))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        st.error("Email already exists. Please use a different email.")
        return False
    finally:
        conn.close()

# Parse field safely
def parse_field(data):
    if not data:
        return []
    try:
        return ast.literal_eval(data)
    except (ValueError, SyntaxError):
        return [item.strip() for item in data.split(",")]

# Predict job recommendations using model
def predict_jobs(user_skills, user_experience):
    user_vector = np.array([user_experience] + [1 if skill in user_skills else 0 for skill in job_model["skills_list"]])
    job_scores = job_model["model"].predict(user_vector.reshape(1, -1))
    return job_model["jobs_df"].iloc[np.argsort(-job_scores[0])[:10]]  # Top 10 jobs

# Dashboard function
def dashboard(email, role):
    st.title("User Dashboard")
    
    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed.")
        return

    cur = conn.cursor()

    st.subheader("Profile Setup")

    cur.execute("""
        SELECT full_name, skills, contact, locations, experience, job_role, salary, industries, job_type 
        FROM users WHERE email = %s
    """, (email,))
    user_data = cur.fetchone()

    full_name = user_data[0] if user_data and user_data[0] else ""
    contact = user_data[2] if user_data and user_data[2] else ""
    experience = user_data[4] if user_data and user_data[4] else 0
    job_role = user_data[5] if user_data and user_data[5] else ""
    salary = user_data[6] if user_data and user_data[6] else ""
    job_type = user_data[8] if user_data and user_data[8] else ""

    skills = parse_field(user_data[1]) if user_data and user_data[1] else []
    locations = parse_field(user_data[3]) if user_data and user_data[3] else []
    industries = parse_field(user_data[7]) if user_data and user_data[7] else []

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
            skills_array = "{" + ",".join(f'"{skill}"' for skill in skills) + "}"
            locations_array = "{" + ",".join(f'"{loc}"' for loc in locations) + "}"
            industries_array = "{" + ",".join(f'"{ind}"' for ind in industries) + "}"
            
            cur.execute("""
                UPDATE users SET full_name = %s, skills = %s, contact = %s, locations = %s, experience = %s, 
                job_role = %s, salary = %s, industries = %s, job_type = %s WHERE email = %s
            """, (full_name, skills_array, contact, locations_array, experience, job_role, salary, industries_array, job_type, email))

            conn.commit()
            st.success("Profile updated successfully!")
        except Exception as e:
            st.error(f"Error updating profile: {e}")

    st.subheader("Job Recommendations")
    if st.button("Get Recommendations"):
        if skills and experience:
            recommended_jobs = predict_jobs(skills, experience)
            for _, job in recommended_jobs.iterrows():
                st.write(f"**{job['title']}** at **{job['company']}** - {job['location']}")
                st.write(f"{job['description']}")
                st.write("---")
        else:
            st.warning("Please update your profile with skills and experience.")
    conn.close()

if __name__ == "__main__":
    main()
