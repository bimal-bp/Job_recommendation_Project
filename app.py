import streamlit as st
import psycopg2
import bcrypt
import streamlit_authenticator as stauth

# Database connection
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

# Streamlit App
st.title("User Authentication System")

# Login Form
email = st.text_input("Email")
password = st.text_input("Password", type="password")
login_button = st.button("Login")

if login_button:
    role = authenticate_user(email, password)
    if role:
        st.success(f"Welcome, {role.capitalize()}!")
        if role == "admin":
            st.write("Admin Dashboard: Upload Market Trends")
            # Admin functionalities here
        else:
            st.write("User Dashboard")
            # User functionalities here
    else:
        st.error("Invalid credentials. Please try again.")

# Signup Form
st.subheader("Create a New Account")
new_email = st.text_input("New Email")
new_password = st.text_input("New Password", type="password")
signup_button = st.button("Sign Up")

if signup_button:
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
