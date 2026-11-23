# 🎓 CSE Project Viva, Architecture & Code Defense Guide
## Project: Modular Gmail Spam Classifier & Mailbox Cleaner

> **Quick Tip for your Test / Viva:** Don't panic! You don't need to be a math genius. Examiners look for whether you understand **how the pieces connect together**, **why you made your design choices**, and **where specific logic lives in your code**. Read this document carefully before your test.

---

## ⚡ 1. The 30-Second Elevator Pitch (Memorize This!)

> *"Our project is an end-to-end, presentation-ready email security system. It connects to a user's real Gmail account, retrieves incoming emails, extracts and cleans the text, and feeds it into a trained Machine Learning pipeline combining **TF-IDF Vectorization** and **Logistic Regression**. The model predicts the probability of the email being spam. If the score exceeds an adjustable threshold, it is flagged as spam. The user can review the threats on an interactive Neo-Brutalist **Streamlit dashboard** and move them into their actual **Gmail Trash** with a single click. Every scanned email is permanently recorded with timestamp and status in an **SQLite3** database for audit logging."*

---

## 📁 2. Every File Explained (Simple Plain English)

| File Name | Plain English Summary | Why It Exists |
| :--- | :--- | :--- |
| **`spam_dataset.csv`** | The raw training data. Contains 100 labeled email samples (`spam` vs `ham`). | Machine Learning needs historical examples to learn patterns of what spam looks like versus normal email. |
| **`train_model.py`** | The training script. Loads the CSV, cleans the text, trains the ML pipeline, prints performance metrics, and saves the trained brain. | Trains the model once and exports it so you don't have to retrain every time the web app opens. |
| **`spam_model.joblib`** | The saved "brain" of the ML classifier. It is a binary file created by `joblib`. | Allows `app.py` to make real-time predictions in milliseconds without waiting minutes for model training. |
| **`database.py`** | The database manager. Uses Python's native `sqlite3` to store and query scan records in `emails.db`. | Ensures emails aren't lost when the app closes and avoids scanning duplicates using unique Gmail `message_id`. |
| **`emails.db`** | The local SQLite database file created automatically by `database.py`. | Stores table `scanned_emails` with columns: sender, subject, date, spam probability, is_spam flag, and status (`INBOX` vs `TRASHED`). |
| **`gmail_service.py`** | The email gateway. Connects to Gmail via Google Cloud OAuth 2.0 or IMAP SSL, reads emails, decodes body text, and trashes messages. | Encapsulates all network communication with Google servers away from the frontend. |
| **`app.py`** | The interactive Streamlit frontend dashboard. | The user interface where users adjust sensitivity sliders, view metrics, click "Scan Inbox", and purge spam to Trash. |
| **`requirements.txt`** | Dependency manifest. Lists all Python packages required to run the project. | Allows anyone to recreate the exact Python environment using `pip install -r requirements.txt`. |
| **`.env`** | Hidden configuration file created on your machine if you choose "Remember credentials". | Stores your Gmail address and App Password locally so you don't have to re-type it every time. |

---

## 🧠 3. Exact Line-by-Line ML Code Map (Where is the ML Code?)

Examiners will often ask: *"Show me where you wrote the ML code."* Here are the exact files, function names, and line numbers:

### In `train_model.py`:

1. **Text Preprocessing & Label Mapping (`load_and_preprocess_data` — Lines 12 to 39):**
   - **Line 20:** `pd.read_csv(dataset_path)` loads the CSV file into a Pandas DataFrame.
   - **Line 21-22:** `.dropna()` removes empty rows, and `.drop_duplicates()` removes repeated emails to prevent training bias.
   - **Line 24-31:** Cleans the text: removes carriage returns (`\r\n`), extra whitespaces, strips edge spaces, and converts all characters to lowercase (`.str.lower()`).
   - **Line 36-37:** Converts text labels (`"spam"` $\rightarrow$ `1`, `"ham"` $\rightarrow$ `0`) using NumPy's `np.where`.

2. **Building the Scikit-Learn Pipeline (`build_pipeline` — Lines 42 to 67):**
   - **Line 47-67:** Combines feature extraction and classifier into a single pipeline:
     - `TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000, sublinear_tf=True)`: Converts raw text into mathematical vectors of words and word pairs (unigrams + bigrams), filtering out common English filler words like *"the"*, *"is"*, *"at"*.
     - `LogisticRegression(random_state=42, C=1.0, solver="liblinear")`: The machine learning classifier that learns the weights of spam words and outputs a probability score between `0.0` and `1.0`.

3. **Evaluating Performance (`evaluate_model` — Lines 70 to 103):**
   - **Line 75:** `model_pipeline.predict(test_features)` tests model predictions against the unseen test data.
   - **Lines 77-80:** Computes **Accuracy**, **Precision**, **Recall**, and **F1-Score**.
   - **Line 82:** `confusion_matrix(test_labels, predicted_labels)` outputs the 2x2 matrix showing True Positives, True Negatives, False Positives, and False Negatives.

4. **Model Serialization / Export (`save_trained_pipeline` — Lines 106 to 113):**
   - **Line 111:** `joblib.dump(model_pipeline, output_path)` saves the trained pipeline into `spam_model.joblib`.

5. **Train / Test Split & Fit (`train_model` — Lines 116 to 137):**
   - **Line 123-129:** `train_test_split(..., test_size=0.25, random_state=42, stratify=target_labels)` splits the data into 75% for training and 25% for testing. `stratify` guarantees equal proportion of spam and ham in both sets.
   - **Line 132:** `pipeline.fit(x_train, y_train)` **$\leftarrow$ THIS IS THE EXACT LINE THAT TRAINS THE ML MODEL!**

---

### In `app.py` (Real-Time Inference):

1. **Loading the Trained Model (`load_spam_model` — Lines 17 to 25):**
   - **Line 24:** `joblib.load(model_path)` deserializes `spam_model.joblib` into memory. Streamlit's `@st.cache_resource` ensures it loads only once for high performance.

2. **Making Live Predictions (`classify_emails` — Lines 28 to 52):**
   - **Line 36-39:** Concatenates email Subject and Body into a single text string.
   - **Line 41:** `probabilities = model_pipeline.predict_proba(text_list)` **$\leftarrow$ THIS COMPUTES THE REAL-TIME SPAM PROBABILITY!**
   - **Line 45:** `spam_probability = float(probabilities[index][1])` extracts the confidence score for Class 1 (Spam).
   - **Line 46:** `is_spam_flag = 1 if spam_probability >= threshold else 0` applies the user's sensitivity slider threshold.

---

## 🔍 4. Which Function Does the Scanning & Which Does the Trashing?

### The Scanning Process:
- **Orchestrator:** `execute_scan()` in [app.py](file:///Users/apple/Documents/CSE%20PROJECT/email/app.py) (Lines 925-961).
  - Fetches the raw emails.
  - Calls `classify_emails()` to score each email using the ML model.
  - Calls `database.insert_scanned_emails_batch()` to save the results in SQLite.
- **Gmail Fetcher (OAuth 2.0 API):** `fetch_inbox_emails()` in [gmail_service.py](file:///Users/apple/Documents/CSE%20PROJECT/email/gmail_service.py) (Lines 132-178). Queries `users().messages().list(userId='me', q='in:inbox')` and parses headers/MIME body.
- **Gmail Fetcher (IMAP Protocol):** `fetch_inbox_emails_imap()` in [gmail_service.py](file:///Users/apple/Documents/CSE%20PROJECT/email/gmail_service.py) (Lines 316-366). Connects to `imap.gmail.com:993` via SSL and fetches messages using RFC822 format.

### The Trashing Process:
- **Orchestrator:** `execute_move_to_trash()` in [app.py](file:///Users/apple/Documents/CSE%20PROJECT/email/app.py) (Lines 645-663).
  - Calls the Gmail service trash handler.
  - Calls `database.update_emails_status_batch()` to update the database column `status = 'TRASHED'`.
- **Gmail API Trash Endpoint:** `move_email_to_trash()` and `move_emails_to_trash_batch()` in [gmail_service.py](file:///Users/apple/Documents/CSE%20PROJECT/email/gmail_service.py) (Lines 180-203). Calls Google's official API: `service.users().messages().trash(userId='me', id=message_id)`.
- **IMAP Trash Handler:** `move_emails_to_trash_imap()` in [gmail_service.py](file:///Users/apple/Documents/CSE%20PROJECT/email/gmail_service.py) (Lines 368-396). Discovers the exact Trash folder using IMAP `SPECIAL-USE` (`find_gmail_trash_folder`), copies the message with `uid("COPY")`, sets `\Deleted` and `\Trash` flags, and expunges.

---

## 🛡️ 5. Why This Tech Stack? (Defense Questions They WILL Ask)

### Question 1: *"Why did you use SQLite instead of MySQL or PostgreSQL?"*
**Answer:**
> *"We chose SQLite3 because this is a desktop email client tool. SQLite is **serverless**, **zero-configuration**, and stores all relational tables directly in a single local file (`emails.db`). MySQL and PostgreSQL are client-server databases intended for multi-user web servers; they require running a background database service, configuring network ports, and managing connection credentials. SQLite gives us full ACID compliance, standard SQL queries, fast indexing, and zero overhead for local desktop storage."*

### Question 2: *"Why did you use a CSV file for training instead of a SQL database?"*
**Answer:**
> *"A CSV (Comma-Separated Values) file is the industry standard for distributing static Machine Learning benchmark datasets. It is lightweight, human-readable, version-controlled with Git, and integrates natively with Pandas via `pd.read_csv()` with C-optimized speed. Once emails are processed at runtime, we store dynamic historical records in our SQLite database."*

### Question 3: *"Why did you use TF-IDF + Logistic Regression instead of Deep Learning (BERT, LSTM, or LLMs)?"*
**Answer:**
> *"Three reasons: **Latency**, **Resource Efficiency**, and **Interpretability**.*
> 1. *BERT or Large Language Models require hundreds of megabytes of GPU VRAM, heavy neural network runtimes (PyTorch/TensorFlow), and take hundreds of milliseconds per email.*
> 2. *TF-IDF with Logistic Regression executes inference in **less than 5 milliseconds** directly on CPU, requires less than 50MB of RAM, and achieved **92% accuracy and 100% spam recall**.*
> 3. *Logistic Regression provides a calibrated mathematical probability between 0 and 1 via the Sigmoid function, allowing users to fine-tune sensitivity using our threshold slider."*

### Question 4: *"Why did you choose Streamlit for the frontend?"*
**Answer:**
> *"Streamlit allows building interactive, data-driven dashboards entirely in Python without the boilerplate of React, HTML, or REST APIs. It provides native state management (`st.session_state`), reactive rerendering on user input, and clean integration with Scikit-Learn and Pandas."*

### Question 5: *"How do you prevent duplicate emails in the database if the user scans twice?"*
**Answer:**
> *"Every email in Gmail has a globally unique `message_id` (e.g., `18c5e9a4f21...`). In our `database.py`, we defined `message_id` as the **PRIMARY KEY**. During insertion, we execute an `INSERT ... ON CONFLICT(message_id) DO UPDATE` query. If the message already exists in SQLite, it does not create a duplicate row; it simply updates the scan timestamp and probability."*

### Question 6: *"What Google OAuth scope did you use, and why?"*
**Answer:**
> *"We used `https://www.googleapis.com/auth/gmail.modify`. Under the Principle of Least Privilege in cyber security, you should only request permissions your app actually needs. `gmail.modify` allows reading inbox messages and moving them to Trash, but **strictly forbids permanent deletion** (`gmail.delete`). This ensures user safety."*

---

## 📊 6. Machine Learning Concepts in Plain English

### A. What is TF-IDF?
- **TF (Term Frequency):** How often a word appears in an email. If *"lottery"* appears 5 times in a short email, it has high TF.
- **IDF (Inverse Document Frequency):** Downweights common words like *"the"*, *"is"*, *"and"* that appear in almost all emails, and upweights rare, suspicious words like *"wire transfer"*, *"bitcoin"*, or *"cryptocurrency"*.
- **Formula Concept:** $\text{TF-IDF} = \text{TF} \times \text{IDF}$. It turns words into numerical importance scores.
- **N-Grams `(1, 2)`:** We analyze single words (*unigrams*) like `"account"` and two-word pairs (*bigrams*) like `"bank account"`, `"password reset"`, `"wire transfer"`.

### B. What is Logistic Regression?
- A classification algorithm that calculates a weighted sum of the TF-IDF feature scores:
  $$z = w_1 x_1 + w_2 x_2 + \dots + b$$
- It passes this value through the **Sigmoid function**:
  $$\sigma(z) = \frac{1}{1 + e^{-z}}$$
- The output is always a probability strictly between `0.0` (100% Ham) and `1.0` (100% Spam).

### C. Why does 100% Spam Recall Matter?
- **Precision:** Of all the emails we flagged as spam, how many were actually spam? (Avoids moving your boss's email to Trash).
- **Recall:** Of all actual spam emails out there, how many did our model catch?
- In spam filtering, **high recall** is critical because you want **zero phishing or fraudulent emails slipping past detection into your inbox**.

---

## 🎯 7. Quick Viva Checklist Before You Present

1. Open your terminal:
   ```bash
   cd "/Users/apple/Documents/CSE PROJECT/email"
   streamlit run app.py
   ```
2. Explain that the app supports both **1-Click Google OAuth** and **App Password (IMAP)**.
3. Show the **Threshold Slider**: explain that moving it from `0.50` to `0.30` makes the filter more aggressive, while `0.80` only flags high-confidence spam.
4. Show the **Live Presentation Email Tester** tab: type *"Your account is locked, click here to verify"* and click *"Run Inference"* to show live real-time scoring.
5. Show the **SQLite Event Log** tab to demonstrate persistent database logging with CSV export.
