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
            cur.execute("SELECT email, COALESCE(full_name, 'N/A'), COALESCE(skills::text, '[]') FROM users LIMIT 10;")
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
st.subheader("User Data")

# Fetch and display user data
users_data = fetch_users()

if users_data:
    for user in users_data:
        email, full_name, skills = user
        st.write(f"**Email:** {email}")
        st.write(f"**Name:** {full_name}")
        
        # Convert skills from string format to list format if necessary
        skills_list = eval(skills) if skills.startswith("[") and skills.endswith("]") else [skills]
        st.write(f"**Skills:** {', '.join(skills_list) if skills_list else 'N/A'}")
        
        st.write("---")
else:
    st.write("No users found.")
