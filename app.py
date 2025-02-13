import pandas as pd

class JobRecommendationSystem:
    def __init__(self, dataset_path):
        self.df = pd.read_csv("final_sample_data.csv")  # Load dataset

    def recommend_jobs(self, title, skills, experience, top_n=5):
        """
        Recommends jobs based on title, skills, and experience.
        """
        # Convert user inputs to lowercase for case-insensitive matching
        title = title.lower()
        skills = skills.lower().split(", ")  # Convert skills to list

        # Filter jobs that match the title (or similar titles)
        filtered_jobs = self.df[self.df["Title"].str.lower().str.contains(title, na=False)]

        # Further filter based on required skills
        filtered_jobs = filtered_jobs[
            filtered_jobs["Skills"].apply(lambda x: any(skill in x.lower() for skill in skills) if pd.notna(x) else False)
        ]

        # Filter jobs where required experience is less than or equal to the user's experience
        filtered_jobs = filtered_jobs[filtered_jobs["Experience"] <= experience]

        # Sort jobs based on relevance (e.g., experience match, skills match)
        filtered_jobs["Skill_Match"] = filtered_jobs["Skills"].apply(lambda x: sum(skill in x.lower() for skill in skills))
        filtered_jobs = filtered_jobs.sort_values(by=["Skill_Match", "Experience"], ascending=[False, True])

import streamlit as st
import pickle

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
def predict_jobs(title, skills, experience):
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

# Button to generate recommendations
if st.button("Get Job Recommendations"):
    if job_title and user_skills and experience >= 0:
        recommended_jobs = predict_jobs(job_title, user_skills, experience)
        st.subheader("Recommended Jobs:")
        if isinstance(recommended_jobs, pd.DataFrame) and not recommended_jobs.empty:
            for index, row in recommended_jobs.iterrows():
                st.write(f"- **Title:** {row['Title']}, **Company:** {row['Company']}, [Apply Here]({row['job_link']})")
        else:
            st.write("No matching jobs found.")
    else:
        st.warning("Please fill out all fields before submitting.")


        # Return top N jobs
        return filtered_jobs[["Title", "Company", "job_link"]].head(top_n)
