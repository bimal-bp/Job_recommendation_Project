import psycopg2
import streamlit as st
import pandas as pd  # Import pandas

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
            cur.execute("SELECT * FROM users;")  
            users = cur.fetchall()
            columns = [desc[0] for desc in cur.description]  # Get column names
            cur.close()
            conn.close()
            
            # Convert to Pandas DataFrame
            df = pd.DataFrame(users, columns=columns)
            return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    return pd.DataFrame()

# Streamlit App
st.title("User Dashboard")
st.subheader("User Data")

# Fetch and display all user data
users_df = fetch_all_users()

if not users_df.empty:
    st.write(f"Total Users: {len(users_df)}")
    st.dataframe(users_df)  # Display as a table
else:
    st.write("No users found.")
