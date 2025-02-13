import pandas as pd
import re
import pickle
import requests
from io import StringIO
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

class JobRecommender:
    def __init__(self, model_path='job_recommendation_system (1).pkl'):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.tfidf = None
        self.df = None
        self.tfidf_matrix = None
        self.model_path = model_path
        self.load_model()

    def clean_text(self, text):
        text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        return ' '.join([self.lemmatizer.lemmatize(word) for word in text.split() if word not in self.stop_words])

    def load_model(self):
        try:
            with open(self.model_path, 'rb') as f:
                loaded_model = pickle.load(f)
                self.df = loaded_model.df
                self.tfidf = loaded_model.tfidf
                self.tfidf_matrix = loaded_model.tfidf_matrix
            print("Pre-trained model loaded successfully.")
        except FileNotFoundError:
            print("No pre-trained model found. Please provide a trained model.")

    def recommend_jobs(self, title, skills, experience, top_n=5):
        if self.df is None or self.tfidf is None or self.tfidf_matrix is None:
            print("Model is not properly loaded.")
            return pd.DataFrame()
        
        query_vec = self.tfidf.transform([self.clean_text(title + ' ' + skills)])
        self.df['Similarity'] = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        recommendations = self.df[self.df['Experience'] <= experience]
        return recommendations.sort_values(by='Similarity', ascending=False).head(top_n)[['Title', 'Company', 'job_link']]

# Get user input
title = input("Enter your desired job title: ")
skills = input("Enter your skills (comma-separated): ")
experience = int(input("Enter your years of experience: "))

# Load pre-trained model and get recommendations
job_recommender = JobRecommender()
recommendations = job_recommender.recommend_jobs(title, skills, experience, top_n=5)
print("\nRecommended Jobs:")
print(recommendations)
