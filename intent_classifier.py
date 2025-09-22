# intent_classifier.py
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import pandas as pd
import joblib

MODEL_NAME = "all-MiniLM-L6-v2"
clf_file = "intent_clf.pkl"
embed = SentenceTransformer(MODEL_NAME)

def train_intent(path="intent_data.csv"):
    df = pd.read_csv(path)
    X = df["text"].tolist()
    y = df["intent"].tolist()
    X_emb = embed.encode(X, convert_to_numpy=True)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_emb, y)
    joblib.dump(clf, clf_file)
    print("Saved intent classifier:", clf_file)

def predict_intent(text):
    import joblib
    clf = joblib.load(clf_file)
    emb = embed.encode([text], convert_to_numpy=True)
    probs = clf.predict_proba(emb)[0]
    label = clf.classes_[probs.argmax()]
    confidence = probs.max()
    return label, float(confidence)

if __name__ == "__main__":
    train_intent()
