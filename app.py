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
    st.title("Dashboard")
    st.write(f"Welcome, {email}!")
    
    if role == "admin":
        st.subheader("Admin Panel")
        st.write("Manage users, upload market trends, and more.")
    else:
        st.subheader("User Dashboard")
        st.write("View job recommendations, saved profiles, and more.")
    
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["email"] = None
        st.session_state["role"] = None
        st.rerun()

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
        option = st.radio("Select Option", ["Login", "Sign Up"])
        
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
                    st.error("Invalid credentials. Please try again.")
        
        elif option == "Sign Up":
            if st.button("Sign Up"):
                if register_user(email, password):
                    st.success("Account created successfully! You can now log in.")
                    st.session_state["logged_in"] = True
                    st.session_state["email"] = email
                    st.session_state["role"] = "user"
                    st.rerun()

if __name__ == "__main__":
    main()
