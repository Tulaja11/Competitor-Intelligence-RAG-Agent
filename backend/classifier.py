import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score

MODEL_PATH = "models/intent_classifier.pkl"
TRAINING_DATA_PATH = "data/training_data.json"


def train_classifier():
    """Train the intent classifier and save it."""
    # Load training data
    with open(TRAINING_DATA_PATH, "r") as f:
        data = json.load(f)

    queries = [item["query"] for item in data]
    labels = [item["label"] for item in data]

    # Build pipeline: TF-IDF vectorizer + Logistic Regression
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 3), lowercase=True, sublinear_tf=True, min_df=1)),
        ("clf", CalibratedClassifierCV(LinearSVC(), cv=3)),
    ])

    # Cross-validation to measure accuracy
    scores = cross_val_score(model, queries, labels, cv=5)
    print(f"Cross-validation accuracy: {scores.mean():.2%} (+/- {scores.std():.2%})")

    # Train on full data
    model.fit(queries, labels)

    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"Model saved to {MODEL_PATH}")
    return model


def load_classifier():
    """Load the saved classifier."""
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def predict_intent(query, model=None):
    """Predict the intent category and confidence for a query."""
    if model is None:
        model = load_classifier()

    # Predict category
    category = model.predict([query])[0]

    # Get confidence (max probability)
    probabilities = model.predict_proba([query])[0]
    confidence = max(probabilities)

    return {"category": category, "confidence": float(confidence)}


if __name__ == "__main__":
    # Train the model
    print("Training classifier...")
    model = train_classifier()

    # Test predictions
    print("\n--- Testing Predictions ---")
    test_queries = [
    "Are they hiring data scientists?",
    "What is their monthly cost?",
    "Did they launch a new app?",
    "What features did they release this month?",
    ]

    for q in test_queries:
        result = predict_intent(q, model)
        print(f"'{q}'")
        print(f"  -> {result['category']} (confidence: {result['confidence']:.2%})\n")