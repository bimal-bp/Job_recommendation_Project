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

# Dashboard page
def dashboard(email, role):
    st.title("User Dashboard")
    st.sidebar.title("Menu")
    
    # Remove "Job Recommendations" from the sidebar menu
    menu_options = ["Profile Setup", "Market Trends"]  # Only "Profile Setup" and "Market Trends" in the sidebar
    
    choice = st.sidebar.radio("Go to", menu_options)

    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed.")
        return

    cur = conn.cursor()

    if choice == "Profile Setup":
        st.subheader("Profile Setup")

        # Fetch existing user data
        cur.execute("SELECT full_name, skills, contact, locations, experience, job_role, salary, industries, job_type FROM users WHERE email = %s", (email,))
        user_data = cur.fetchone()

        # Default values if no data exists
        full_name = user_data[0] if user_data and user_data[0] else ""
        skills = ast.literal_eval(user_data[1]) if user_data and user_data[1] else []
        contact = user_data[2] if user_data and user_data[2] else ""
        locations = ast.literal_eval(user_data[3]) if user_data and user_data[3] else []
        experience = user_data[4] if user_data and user_data[4] else 0
        job_role = user_data[5] if user_data and user_data[5] else ""
        salary = user_data[6] if user_data and user_data[6] else ""
        industries = ast.literal_eval(user_data[7]) if user_data and user_data[7] else []
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

        # Add "Job Recommendations" button below the "Profile Setup" section
        if st.button("Job Recommendations"):
            st.subheader("Job Recommendations")
            st.write("Coming soon...")

    elif choice == "Market Trends":
        st.subheader("Market Trends")
        
        # Fetch and display market trends
        cur.execute("SELECT trend FROM market_trends ORDER BY id DESC")  # Assuming you have a market_trends table
        trends = cur.fetchall()
        
        if trends:
            st.write("Latest Market Trends:")
            for trend in trends:
                st.write(f"- {trend[0]}")
        else:
            st.write("No market trends available.")
        
        # Allow only admins to submit new trends
        if role == "admin":
            trend_input = st.text_area("Enter Market Trends")
            if st.button("Submit Trends"):
                if trend_input:
                    try:
                        cur.execute("INSERT INTO market_trends (trend) VALUES (%s)", (trend_input,))
                        conn.commit()
                        st.success("Market trends submitted successfully!")
                    except Exception as e:
                        st.error(f"Error submitting trends: {e}")
                else:
                    st.error("Please enter some text before submitting.")

    conn.close()

# Main function
def main():
    st.title("User Authentication System")
    
    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["email"] = None
        st.session_state["role"] = None
    
    if st.session_state["logged_in"]:
        dashboard(st.session_state["email"], st.session_state["role"])
    else:
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
                    st.rerun()  # Refresh the page to show the dashboard
                else:
                    st.error("Invalid email or password.")
        elif option == "Sign Up":
            if st.button("Sign Up"):
                if register_user(email, password):
                    st.success("Registration Successful! Please login.")
                else:
                    st.error("Registration failed. Please try again.")
        elif option == "Admin Login":
            admin_password = st.text_input("Admin Password", type="password")
            if st.button("Admin Login"):
                if admin_password == "admin123":  # Replace with a secure password or database check
                    st.session_state["logged_in"] = True
                    st.session_state["email"] = "admin@example.com"
                    st.session_state["role"] = "admin"
                    st.rerun()
                else:
                    st.error("Invalid admin password.")

# Run the main function
if __name__ == "__main__":
    main()
