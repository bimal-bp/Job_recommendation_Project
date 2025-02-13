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

# Function to fetch all user data
def fetch_all_users():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Fetch all data from the users table
            cur.execute("SELECT * FROM users;")  # Fetch all rows
            users = cur.fetchall()
            columns = [desc[0] for desc in cur.description]  # Get column names
            cur.close()
            conn.close()
            return users, columns
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return [], []
    return [], []

# Streamlit App
st.title("User Dashboard")
st.subheader("User Data")

# Fetch and display all user data
users_data, columns = fetch_all_users()

if users_data:
    st.write(f"Total Users: {len(users_data)}")
    
    # Display data as a table
    st.dataframe(users_data, columns=columns)

else:
    st.write("No users found.")
