import pandas as pd
import streamlit as st
import pickle

# Load dataset directly
@st.cache_resource
def load_dataset():
    try:
        df = pd.read_csv("final_sample_data.csv")  # Load dataset
        return df
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return None

# Job Recommendation System Class
class JobRecommendationSystem:
    def __init__(self, df):
        self.df = df  # Use the loaded dataset directly

    def recommend_jobs(self, title, skills, experience, top_n=5):
        """
        Recommends jobs based on title, skills, and experience.
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame()  # Return empty DataFrame if dataset is not loaded

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

        # Return top N jobs
        return filtered_jobs[["Title", "Company", "job_link"]].head(top_n)


# Load dataset
df = load_dataset()

# Initialize model with dataset
if df is not None:
    model = JobRecommendationSystem(df)
else:
    model = None

# Streamlit UI
st.title("🔍 Job Recommendation System")
st.subheader("Find the Best Job Matches for You")

# User input for job recommendation
job_title = st.text_input("Enter Job Title:", placeholder="e.g., Developer")
user_skills = st.text_area("Enter Your Skills (comma-separated):", placeholder="e.g., Python, SQL")
experience = st.number_input("Enter Years of Experience:", min_value=0, max_value=50, value=1)

# Button to generate recommendations
if st.button("Get Job Recommendations"):
    if model and job_title and user_skills and experience >= 0:
        recommended_jobs = model.recommend_jobs(job_title, user_skills, experience)

        st.subheader("📌 Recommended Jobs:")
        if not recommended_jobs.empty:
            for index, row in recommended_jobs.iterrows():
                st.write(f"- **Title:** {row['Title']}, **Company:** {row['Company']}, [Apply Here]({row['job_link']})")
        else:
            st.write("❌ No matching jobs found.")
    else:
        st.warning("⚠️ Please fill out all fields before submitting.")
