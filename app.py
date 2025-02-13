import psycopg2
import streamlit as st

# Function to establish a database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="neondb",
            user="neondb_owner",
            password="npg_hnmkC3SAi7Lc",
            host="ep-steep-dawn-a87fu2ow-pooler.eastus2.azure.neon.tech",
            port="5432",
            sslmode="require"
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Function to fetch user data from the database
def fetch_users():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT email, full_name, skills FROM users LIMIT 10;")
            users = cur.fetchall()
            cur.close()
            conn.close()
            return users
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return []
    return []

# Streamlit App
st.title("User Dashboard")

# Fetch and display user data
st.subheader("User Data")
users_data = fetch_users()

if users_data:
    for user in users_data:
        st.write(f"**Email:** {user[0]}")
        st.write(f"**Name:** {user[1]}")
        st.write(f"**Skills:** {user[2]}")
        st.write("---")
else:
    st.write("No users found.")
