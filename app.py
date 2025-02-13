import pandas as pd
import pickle
import streamlit as st

# Load your dataset
df = pd.read_csv('final_sample_data.csv')  # Ensure this file exists in the correct path

# Initialize and preprocess the model
class JobRecommendationSystem:
    def preprocess_data(self, df):
        pass  # Implement preprocessing logic

    def recommend_jobs(self, title, skills, experience, top_n=5):
        # Implement job recommendation logic
        return pd.DataFrame([
            {"Title": "Data Scientist", "Company": "XYZ Corp", "job_link": "http://example.com"},
            {"Title": "ML Engineer", "Company": "ABC Inc", "job_link": "http://example.com"}
        ])

model = JobRecommendationSystem()
model.preprocess_data(df)

# Save the model
with open('job_recommendation_system.pkl', 'wb') as f:
    pickle.dump(model, f)

# Load the trained job recommendation model
@st.cache_resource
def load_model():
    try:
        with open("job_recommendation_system.pkl", "rb") as model_file:
            return pickle.load(model_file)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None 

# Function to predict job recommendations
def predict_jobs(title, skills, experience, salary):
    model = load_model()
    if model is None:
        return ["Model loading failed. No recommendations available."]

    # Ensure the model has the required method
    if hasattr(model, "recommend_jobs"):
        try:
            recommendations = model.recommend_jobs(title, skills, experience, top_n=5)
            return recommendations
        except Exception as e:
            st.error(f"Error in prediction: {e}")
            return ["Prediction failed."]
    else:
        st.error("The loaded model does not have a 'recommend_jobs' method.")
        return ["Model error."]

# Streamlit UI
st.title("Job Recommendation System")
st.subheader("Find the Best Job Matches for You")

# User input for job recommendation
job_title = st.text_input("Enter Job Title:", placeholder="e.g., Developer")
user_skills = st.text_area("Enter Your Skills (comma-separated):", placeholder="e.g., Python, SQL")
experience = st.number_input("Enter Years of Experience:", min_value=0, max_value=50, value=1)
salary = st.number_input("Expected Salary (in LPA):", min_value=0, value=5)

# Button to generate recommendations
if st.button("Get Job Recommendations"):
    if job_title and user_skills and experience >= 0 and salary >= 0:
        recommended_jobs = predict_jobs(job_title, user_skills, experience, salary)
        st.subheader("Recommended Jobs:")
        if isinstance(recommended_jobs, pd.DataFrame):
            for _, row in recommended_jobs.iterrows():
                st.write(f"- **Title:** {row['Title']}, **Company:** {row['Company']}, **Link:** {row['job_link']}")
        else:
            st.write(recommended_jobs[0])  # Show error message if any
    else:
        st.warning("Please fill out all fields before submitting.")
