import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans

# 1. Classification Model Initialization
vectorizer = TfidfVectorizer()
clf = RandomForestClassifier()

def train_classification():
    # Expanded training data for better accuracy
    X_train = [
        "The cell is the basic unit of life", "Photosynthesis in plants", # Biology
        "Solve the following quadratic equations", "Calculate the area of circle", # Mathematics
        "Newton's laws of motion and gravity", "Electromagnetic induction", # Physics
        "Data Base Management System and SQL", "Computer networks and security", # Computer Science
        "Chemical reactions and periodic table", "Atomic structure and bonding" # Chemistry
    ]
    y_train = [
        "Biology", "Biology", 
        "Mathematics", "Mathematics", 
        "Physics", "Physics", 
        "Computer Science", "Computer Science",
        "Chemistry", "Chemistry"
    ]
    
    # Transform text and train the Random Forest model
    X_v = vectorizer.fit_transform(X_train)
    clf.fit(X_v, y_train)

# 2. Regression Model Initialization (Predicting Latency)
reg = LinearRegression()

def train_regression():
    # Training data: Number of words vs Processing time in seconds
    X_len = np.array([[5], [10], [20], [50], [100]]) 
    y_time = np.array([0.2, 0.5, 1.0, 2.5, 5.0])    
    reg.fit(X_len, y_time)

# 3. Clustering Logic (Grouping similar content)
def get_clusters(text_list):
    if len(text_list) < 2: return [0]
    vec = TfidfVectorizer()
    X = vec.fit_transform(text_list)
    km = KMeans(n_components=2, n_init=10)
    km.fit(X)
    return km.labels_

# Execute training on startup
train_classification()
train_regression()

def process_ai(text):
    """
    Main AI engine function.
    Processes the input text to return Subject and Predicted Latency.
    """
    if not text.strip():
        return "Unknown", 0.0
        
    # Classification: Identify the subject
    X_input = vectorizer.transform([text])
    sub = clf.predict(X_input)[0]
    
    # Regression: Predict latency based on word count
    word_count = len(text.split())
    time_pred = reg.predict([[word_count]])[0]
    
    # Ensuring time prediction isn't negative
    final_time = max(0.1, round(float(time_pred), 2))
    
    return sub, final_time

