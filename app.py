import streamlit as st
import psycopg2
import bcrypt
import ast  # To convert database array strings into Python lists

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
    if data is None:
        return []
    if isinstance(data, str):
        try:
            # Try to evaluate as a Python list (if stored as a string representation)
            return ast.literal_eval(data)
        except (ValueError, SyntaxError):
            # Fallback to splitting by commas
            return [item.strip() for item in data.split(",")]
    elif isinstance(data, list):
        return data
    return []

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

    if user_data is None:
        st.error("User data not found.")
        conn.close()
        return

    # Safely parse fields
    full_name = user_data[0] if user_data[0] else ""
    skills = parse_field(user_data[1])  # Handle None or empty skills
    contact = user_data[2] if user_data[2] else ""
    locations = parse_field(user_data[3])  # Handle None or empty locations
    experience = user_data[4] if user_data[4] else 0
    job_role = user_data[5] if user_data[5] else ""
    salary = user_data[6] if user_data[6] else ""
    industries = parse_field(user_data[7])  # Handle None or empty industries
    job_type = user_data[8] if user_data[8] else ""

    # Input fields for profile update
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
            # Convert lists to PostgreSQL array format
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
        cur.execute("SELECT skills, locations FROM users WHERE email = %s", (email,))
        user_profile = cur.fetchone()

        if user_profile:
            user_skills = parse_field(user_profile[0])
            user_locations = parse_field(user_profile[1])
            
            if not user_skills or not user_locations:
                st.warning("Please update your profile with skills and preferred locations.")
            else:
                cur.execute("""
                    SELECT title, company, location, description FROM jobs
                    WHERE location = ANY(%s) AND skills && %s
                    ORDER BY similarity(description, %s) DESC LIMIT 10
                """, (user_locations, user_skills, " ".join(user_skills)))
                recommended_jobs = cur.fetchall()

                if recommended_jobs:
                    st.write("Here are some jobs that match your profile:")
                    for job in recommended_jobs:
                        st.write(f"**{job[0]}** at **{job[1]}** - {job[2]}")
                        st.write(f"{job[3]}")
                        st.write("---")
                else:
                    st.write("No matching jobs found.")
    conn.close()

# Main function
def main():
    st.title("User Authentication System")
    if "logged_in" not in st.session_state:
        st.session_state.update({"logged_in": False, "email": None, "role": None})
    
    if st.session_state["logged_in"]:
        dashboard(st.session_state["email"], st.session_state["role"])
    else:
        option = st.radio("Select Option", ["Login", "Sign Up", "Admin Login"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if option == "Login" and st.button("Login"):
            role = authenticate_user(email, password)
            if role:
                st.session_state.update({"logged_in": True, "email": email, "role": role})
                st.rerun()
            else:
                st.error("Invalid email or password.")
        elif option == "Sign Up" and st.button("Sign Up"):
            if register_user(email, password):
                st.success("Registration Successful! Please login.")

if __name__ == "__main__":
    main()
