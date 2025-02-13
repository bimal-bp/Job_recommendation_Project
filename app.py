import psycopg2
import streamlit as st
import pandas as pd
import pickle  # Load the trained model
import numpy as np

# Load the trained job recommendation model
@st.cache_resource
def load_model():
    try:
        with open("job_recommendation_system.pkl", "rb") as model_file:
            return pickle.load(model_file)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

# Function to establish a database connection
@st.cache_resource
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
        st.error(f"Database connection failed: {e}")
        return None

# Function to fetch all user data
def fetch_all_users():
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()  # Return empty DataFrame if connection fails

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users;")  
            users = cur.fetchall()
            columns = [desc[0] for desc in cur.description]  # Extract column names
            
            return pd.DataFrame(users, columns=columns) if users else pd.DataFrame(columns=columns)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
    finally:
        conn.close()

# Function to predict job recommendations
def predict_jobs(title, skills, experience, salary):
    model = load_model()
    if model is None:
        return ["Model loading failed. No recommendations available."]
    
    # Create a feature array based on input
    input_data = np.array([[title, skills, experience, salary]])

    try:
        predictions = model.predict(input_data)  # Predict job recommendations
        return predictions
    except Exception as e:
        st.error(f"Error in prediction: {e}")
        return ["Prediction failed."]

# Streamlit App
st.title("Job Recommendation System")
st.subheader("Find the Best Job Matches for You")

# User input for job recommendation
job_title = st.text_input("Enter Job Title:")
user_skills = st.text_area("Enter Your Skills (comma-separated):")
experience = st.number_input("Enter Years of Experience:", min_value=0, max_value=50, value=1)
salary = st.number_input("Expected Salary:", min_value=0, value=50000)

# Button to generate recommendations
if st.button("Get Job Recommendations"):
    if job_title and user_skills and experience >= 0 and salary >= 0:
        recommended_jobs = predict_jobs(job_title, user_skills, experience, salary)
        st.subheader("Recommended Jobs:")
        for job in recommended_jobs:
            st.write(f"- {job}")
    else:
        st.warning("Please fill out all fields before submitting.")

# Fetch and display all user data
st.subheader("User Data")
users_df = fetch_all_users()

if not users_df.empty:
    st.write(f"**Total Users:** {len(users_df)}")
    st.dataframe(users_df)  # Display table
else:
    st.warning("No users found.")
