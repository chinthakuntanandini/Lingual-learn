import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans

# 1. Classification Model Initialization
# TfidfVectorizer converts text into numerical features
vectorizer = TfidfVectorizer()
# RandomForest is used to categorize the teacher's speech into subjects
clf = RandomForestClassifier()

def train_classification():
    # Training dataset: Sample sentences and their corresponding subject labels
    X_train = ["The cell is basic unit", "Solve x and y", "Gravity pulls objects", "Python coding"]
    y_train = ["Biology", "Mathematics", "Physics", "Computer Science"]
    
    # Transform text data into numerical vectors
    X_v = vectorizer.fit_transform(X_train)
    # Train the classifier model
    clf.fit(X_v, y_train)

# 2. Regression Model Initialization
# LinearRegression is used to predict processing time (Latency)
reg = LinearRegression()

def train_regression():
    # X_len represents word count in a sentence, y_time represents actual processing time in seconds
    X_len = np.array([[5], [10], [15], [20]]) 
    y_time = np.array([0.5, 1.0, 1.5, 2.0])    
    # Train the model to learn the relationship between sentence length and time
    reg.fit(X_len, y_time)

# 3. Clustering Logic for Post-Class Summary
def get_clusters(text_list):
    # Clustering requires at least two data points (sentences)
    if len(text_list) < 2: return [0]
    
    vec = TfidfVectorizer()
    X = vec.fit_transform(text_list)
    
    # K-Means groups similar sentences into thematic clusters (e.g., Topic A and Topic B)
    km = KMeans(n_components=2)
    km.fit(X)
    return km.labels_ # Returns the cluster index for each sentence

# Initialize and train models on startup
train_classification()
train_regression()

def process_ai(text):
    """
    Main function to process teacher's speech through the ML pipeline.
    Returns: Detected Subject (Classification) and Predicted Time (Regression).
    """
    # Prediction: Identify the subject of the speech
    sub = clf.predict(vectorizer.transform([text]))[0]
    
    # Prediction: Estimate latency based on sentence word count
    word_count = len(text.split())
    time_pred = reg.predict([[word_count]])[0]
    
    return sub, round(time_pred, 2)