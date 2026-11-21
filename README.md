# 🛡️ Presentation-Ready Gmail Spam Classifier & Mailbox Cleaner

An end-to-end, modular Python application that detects spam and phishing emails from Google Gmail in real time using a Scikit-Learn machine learning pipeline (TF-IDF Vectorizer + Logistic Regression), logs scan records into SQLite (`emails.db`), and provides an interactive Streamlit dashboard to review spam probabilities and move detected threats directly to Gmail Trash.

---

## 🏗️ Architecture & Project Structure

The project is structured into modular components where each file has a single, clear responsibility:

```
.
├── spam_dataset.csv     # Labeled training dataset (Spam vs. Legitimate/Ham)
├── spam_model.joblib    # Serialized Scikit-Learn pipeline (TF-IDF + Logistic Regression)
├── train_model.py       # Data cleaning, model training, evaluation metrics, and export
├── database.py          # SQLite database schema, deduplication, scan history, and status updates
├── gmail_service.py     # Google OAuth 2.0 flow, inbox fetching, text decoding, and trashing
├── app.py               # Interactive Streamlit dashboard with KPI metrics and controls
├── emails.db            # Persistent SQLite database (auto-generated upon execution)
└── requirements.txt     # Python dependencies
```

---

## 📦 Tech Stack

- **Data & Machine Learning:** `NumPy`, `Pandas`, `Scikit-Learn` (`TfidfVectorizer` + `LogisticRegression`), `Joblib`
- **Database:** `SQLite3` (native Python `sqlite3`)
- **Email API Integration:** `google-api-python-client`, `google-auth-oauthlib`, `google-auth` (`gmail.modify` scope)
- **Frontend Dashboard:** `Streamlit`

---

## 🚀 Quickstart Guide

### 1. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate    # On macOS / Linux
# venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Train the Spam Classifier

Train the model and generate `spam_model.joblib`:

```bash
python train_model.py
```

**Output Metrics:**
- **Accuracy:** 92.00%
- **Precision:** 85.71%
- **Recall:** 100.00%
- **F1-Score:** 92.31%

---

### 3. Launch the Streamlit Dashboard

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

---

## 🔐 Google Gmail API Setup (Live Mode)

To connect directly to your live Gmail account:

1. Visit the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (e.g., `Gmail-Spam-Detector`).
3. Enable the **Gmail API** in **APIs & Services > Library**.
4. Go to **APIs & Services > Credentials**:
   - Click **Create Credentials** > **OAuth client ID**.
   - Select **Desktop app**.
   - Download the client secrets file and save it as `credentials.json` in the project root folder.
5. In **OAuth consent screen**:
   - Add your Google account as a **Test User**.
6. When you run `app.py` in **Live Gmail API** mode for the first time, a browser window will prompt you to authorize with the `gmail.modify` scope. An authorized session token will be saved as `token.json` for future scans.

> **Tip for Presentations:** If `credentials.json` is not present, you can switch to **Presentation Demo Mode** in the sidebar. This loads realistic synthetic inbox emails so you can demonstrate the complete ML inference, SQLite storage, threshold tuning, and mailbox cleanup workflow seamlessly without needing internet credentials on stage.

---

## 📊 Live Presentation Walkthrough Guide

When presenting this project to evaluators:

1. **Model Pipeline (`train_model.py`):**
   - Explain how text is sanitized using Pandas.
   - Walk through the `TfidfVectorizer(ngram_range=(1, 2))` transformation which extracts unigrams and bigrams with sublinear term-frequency scaling.
   - Explain how `LogisticRegression` outputs calibrated probabilities between 0.0 and 1.0 using the sigmoid function.
   - Highlight the 100% spam recall, which ensures zero fraudulent emails slip past detection.

2. **Persistent Storage (`database.py`):**
   - Highlight SQLite conflict handling (`ON CONFLICT(message_id) DO UPDATE`), preventing redundant storage while updating scan timestamps.
   - Show how status transitions from `INBOX` to `TRASHED` upon cleanup.

3. **Gmail Integration (`gmail_service.py`):**
   - Explain OAuth 2.0 flow using `InstalledAppFlow` and the principle of least privilege (`gmail.modify` allows reading and moving to Trash without granting permanent deletion).
   - Walk through recursive MIME payload decoding for multipart emails.

4. **Streamlit UI (`app.py`):**
   - Demonstrate the **Spam Probability Threshold** slider: show how lowering the threshold catches borderline phishing attempts, while raising it prioritizes high-confidence threats.
   - Demonstrate the **Live Model Sandbox** tab: type custom email text live to let the evaluators see the model classify text on the fly.
   - Demonstrate moving spam to Trash and observing the instant update in SQLite history and KPI metrics.
