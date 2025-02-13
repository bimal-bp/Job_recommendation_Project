import streamlit as st
import psycopg2
import bcrypt
import pickle
import pandas as pd
import ast  # To safely convert stored array strings into lists



# Load the job recommendation model
def load_model():
    try:
        with open("job_recommendation_system.pkl", "rb") as file:
            return pickle.load(file)
    except Exception as e:
        st.error(f"Error loading job recommendation model: {e}")
        return None

model = load_model()

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
    try:
        cur.execute("SELECT password, role FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user and check_password(password, user[0]):
            return user[1]  # Return role (user/admin)
        return None
    except Exception as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        conn.close()

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
    except Exception as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        return False
    finally:
        conn.close()

# Job Recommendations
def get_job_recommendations(user_profile):
    if not model:
        return []
    
    user_df = pd.DataFrame([user_profile])
    recommendations = model.predict(user_df)
    return recommendations

# Convert Python lists to PostgreSQL array format
def to_postgres_array(python_list):
    return "{" + ",".join(python_list) + "}"

# Dashboard page
def dashboard(email, role):
    st.title("User Dashboard")
    st.sidebar.title("Menu")

    menu_options = ["Profile Setup", "Market Trends"]
    choice = st.sidebar.radio("Go to", menu_options)

    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed.")
        return

    cur = conn.cursor()

    if choice == "Profile Setup":
        st.subheader("Profile Setup")

        # Fetch user data
        try:
            cur.execute("SELECT full_name, skills, contact, locations, experience, job_role, salary, industries, job_type FROM users WHERE email = %s", (email,))
            user_data = cur.fetchone()
        except Exception as e:
            conn.rollback()
            st.error(f"Database error: {e}")
            return

        # Convert database fields properly
        full_name = user_data[0] if user_data and user_data[0] else ""
        contact = user_data[2] if user_data and user_data[2] else ""
        experience = user_data[4] if user_data and user_data[4] else 0
        job_role = user_data[5] if user_data and user_data[5] else ""
        salary = user_data[6] if user_data and user_data[6] else ""

        # Convert skills, locations, and industries safely
        def safe_eval(data):
            try:
                result = ast.literal_eval(data) if data else []
                return result if isinstance(result, list) else []
            except (ValueError, SyntaxError):
                return []

        skills = safe_eval(user_data[1])
        locations = safe_eval(user_data[3])
        industries = safe_eval(user_data[7])
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
                # Convert skills, locations, and industries to PostgreSQL array format
                skills_array = to_postgres_array(skills)
                locations_array = to_postgres_array(locations)
                industries_array = to_postgres_array(industries)

                cur.execute("""
                    UPDATE users SET full_name = %s, skills = %s, contact = %s, locations = %s, experience = %s, 
                    job_role = %s, salary = %s, industries = %s, job_type = %s WHERE email = %s
                """, (full_name, skills_array, contact, locations_array, experience, job_role, salary, industries_array, job_type, email))
                conn.commit()
                st.success("Profile updated successfully!")
            except Exception as e:
                conn.rollback()
                st.error(f"Error updating profile: {e}")

        # Job Recommendations Section
        st.subheader("Job Recommendations")

        # Fetch user profile again
        try:
            cur.execute("SELECT skills, experience, job_role, industries FROM users WHERE email = %s", (email,))
            user_data = cur.fetchone()
        except Exception as e:
            conn.rollback()
            st.error(f"Database error: {e}")
            return

        if user_data:
            skills = safe_eval(user_data[0])
            experience = user_data[1]
            job_role = user_data[2]
            industries = safe_eval(user_data[3])

            # Create input data for model
            user_profile = {
                "skills": " ".join(skills),
                "experience": experience,
                "job_role": job_role,
                "industries": " ".join(industries)
            }

            # Get recommendations
            recommendations = get_job_recommendations(user_profile)
            if recommendations:
                st.write("Recommended Jobs:")
                for job in recommendations:
                    st.write(f"- {job}")
            else:
                st.write("No job recommendations available.")

    elif choice == "Market Trends":
        st.subheader("Market Trends")
        try:
            cur.execute("SELECT trend FROM market_trends ORDER BY id DESC")
            trends = cur.fetchall()
        except Exception as e:
            conn.rollback()
            st.error(f"Database error: {e}")
            return

        if trends:
            st.write("Latest Market Trends:")
            for trend in trends:
                st.write(f"- {trend[0]}")
        else:
            st.write("No market trends available.")

    conn.close()

# Main function
def main():
    st.title("User Authentication System")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["email"] = None
        st.session_state["role"] = None

    if st.session_state["logged_in"]:
        dashboard(st.session_state["email"], st.session_state["role"])
    else:
        option = st.radio("Select Option", ["Login", "Sign Up"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if option == "Login" and st.button("Login"):
            role = authenticate_user(email, password)
            if role:
                st.session_state.update({"logged_in": True, "email": email, "role": role})
                st.rerun()
        elif option == "Sign Up" and st.button("Sign Up"):
            if register_user(email, password):
                st.success("Registration successful! Please log in.")

if __name__ == "__main__":
    main()
