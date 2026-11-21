import os
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def load_and_preprocess_data(dataset_path="spam_dataset.csv"):
    """
    Loads email records from CSV, cleans text using Pandas and NumPy, and maps labels.
    Takes the dataset file path string and returns cleaned text Series and binary label Series.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")

    dataframe = pd.read_csv(dataset_path)
    dataframe = dataframe.dropna(subset=["text", "label"])
    dataframe = dataframe.drop_duplicates(subset=["text"])

    dataframe["cleaned_text"] = (
        dataframe["text"]
        .astype(str)
        .str.replace(r"\r\n|\r|\n", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.lower()
    )

    valid_mask = dataframe["cleaned_text"].str.len() > 0
    dataframe = dataframe[valid_mask]

    label_series = dataframe["label"].astype(str).str.strip().str.lower()
    binary_labels = np.where(label_series == "spam", 1, 0)

    return dataframe["cleaned_text"], pd.Series(binary_labels, index=dataframe.index)


def build_pipeline():
    """
    Constructs a Scikit-Learn Pipeline combining TF-IDF Vectorizer and Logistic Regression.
    Takes no inputs and returns an un-fitted Scikit-Learn Pipeline instance.
    """
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    stop_words="english",
                    ngram_range=(1, 2),
                    max_features=5000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    random_state=42,
                    C=1.0,
                    solver="liblinear",
                ),
            ),
        ]
    )


def evaluate_model(model_pipeline, test_features, test_labels):
    """
    Evaluates pipeline predictions against ground truth labels and prints performance metrics.
    Takes the fitted pipeline, test text features, and true binary labels, returning a metrics dict.
    """
    predicted_labels = model_pipeline.predict(test_features)

    accuracy = float(accuracy_score(test_labels, predicted_labels))
    precision = float(precision_score(test_labels, predicted_labels, zero_division=0))
    recall = float(recall_score(test_labels, predicted_labels, zero_division=0))
    f1 = float(f1_score(test_labels, predicted_labels, zero_division=0))
    report = classification_report(test_labels, predicted_labels, target_names=["Ham (0)", "Spam (1)"])
    conf_matrix = confusion_matrix(test_labels, predicted_labels)

    separator = "=" * 60
    print(separator)
    print("GMAIL SPAM CLASSIFIER - MODEL EVALUATION METRICS")
    print(separator)
    print(f"Accuracy  : {accuracy * 100:.2f}%")
    print(f"Precision : {precision * 100:.2f}%")
    print(f"Recall    : {recall * 100:.2f}%")
    print(f"F1-Score  : {f1 * 100:.2f}%")
    print(separator)
    print("Classification Report:\n", report)
    print("Confusion Matrix:\n", conf_matrix)
    print(separator)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": conf_matrix,
    }


def save_trained_pipeline(model_pipeline, output_path="spam_model.joblib"):
    """
    Serializes and saves the trained Scikit-Learn pipeline to disk using Joblib.
    Takes the fitted pipeline object and destination file path, returning the output path string.
    """
    joblib.dump(model_pipeline, output_path)
    print(f"Successfully saved trained model pipeline to: {output_path}")
    return output_path


def train_model(dataset_path="spam_dataset.csv", model_output_path="spam_model.joblib"):
    """
    Orchestrates dataset loading, train-test splitting, model training, evaluation, and saving.
    Takes dataset path and model output path, returning the fitted pipeline and metrics dictionary.
    """
    text_features, target_labels = load_and_preprocess_data(dataset_path)

    x_train, x_test, y_train, y_test = train_test_split(
        text_features,
        target_labels,
        test_size=0.25,
        random_state=42,
        stratify=target_labels,
    )

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)

    metrics = evaluate_model(pipeline, x_test, y_test)
    save_trained_pipeline(pipeline, model_output_path)

    return pipeline, metrics


if __name__ == "__main__":
    train_model()
