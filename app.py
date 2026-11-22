import os
import joblib
import pandas as pd
import streamlit as st
import database
import gmail_service

st.set_page_config(
    page_title="Gmail Spam Cleaner",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def load_spam_model(model_path="spam_model.joblib"):
    """
    Loads and caches the trained Scikit-Learn spam classification pipeline from disk using Joblib.
    Takes the model file path string and returns the deserialized Scikit-Learn pipeline object.
    """
    if not os.path.exists(model_path):
        return None
    return joblib.load(model_path)


def classify_emails(model_pipeline, email_records, threshold=0.50):
    """
    Predicts spam probabilities for a list of emails and flags messages exceeding the threshold.
    Takes the model pipeline, list of email dictionaries, and float threshold, returning enriched records.
    """
    if not email_records:
        return []

    text_list = [
        f"{email.get('subject', '')} {email.get('body', '')}".strip()
        for email in email_records
    ]

    probabilities = model_pipeline.predict_proba(text_list)

    enriched_records = []
    for index, email in enumerate(email_records):
        spam_probability = float(probabilities[index][1])
        is_spam_flag = 1 if spam_probability >= threshold else 0

        updated_email = dict(email)
        updated_email["spam_probability"] = round(spam_probability, 4)
        updated_email["is_spam"] = is_spam_flag
        enriched_records.append(updated_email)

    return enriched_records


def inject_neo_brutalist_styling():
    """
    Injects high-contrast neo-brutalist styling ensuring transparent alert backgrounds and readable text.
    Takes no inputs and injects custom CSS rules directly into the page DOM.
    """
    neo_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900&display=swap');

        body, button, input, textarea, select, label, h1, h2, h3, h4, h5, h6, p {
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
            color: #1a1a1a !important;
        }

        [class*="stIcon"], .material-symbols-rounded, [data-testid="stIcon"], [data-baseweb="icon"] {
            font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        }

        .stApp {
            background-color: #f5f0e6 !important;
            color: #1a1a1a !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #ede7dc !important;
            border-right: 2.5px solid #1a1a1a !important;
        }

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div {
            color: #1a1a1a !important;
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] label p,
        div[data-testid="stRadio"] span,
        div[data-testid="stCheckbox"] label,
        div[data-testid="stCheckbox"] label p,
        div[data-testid="stCheckbox"] span,
        div[data-testid="stWidgetLabel"],
        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stWidgetLabel"] span {
            color: #1a1a1a !important;
            font-weight: 800 !important;
            font-size: 0.95rem !important;
        }

        div[data-testid="stAlert"] {
            border: 2.5px solid #1a1a1a !important;
            border-radius: 16px !important;
            box-shadow: 4px 4px 0px #1a1a1a !important;
            background-color: #fef08a !important;
            padding: 14px 18px !important;
        }

        div[data-testid="stAlert"] > div,
        div[data-testid="stAlert"] [data-baseweb="notification"],
        div[data-testid="stAlert"] [role="alert"] {
            background-color: transparent !important;
            color: #1a1a1a !important;
        }

        div[data-testid="stAlert"] * {
            color: #1a1a1a !important;
            font-weight: 800 !important;
            font-size: 0.95rem !important;
        }

        div[data-testid="stExpander"] {
            border: 2.5px solid #1a1a1a !important;
            border-radius: 16px !important;
            background-color: #fffdf5 !important;
            box-shadow: 3.5px 3.5px 0px #1a1a1a !important;
            margin-bottom: 14px;
        }

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary span,
        div[data-testid="stExpander"] summary p {
            color: #1a1a1a !important;
            font-weight: 800 !important;
        }

        div[data-testid="stExpander"] div,
        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] li {
            color: #1a1a1a !important;
            font-weight: 600 !important;
        }

        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 700 !important;
            background-color: #ffffff !important;
            border: 2.5px solid #1a1a1a !important;
            color: #1a1a1a !important;
            border-radius: 14px !important;
            box-shadow: 3px 3px 0px #1a1a1a !important;
            padding: 12px 14px !important;
        }

        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {
            color: #71717a !important;
            font-weight: 500 !important;
            opacity: 1 !important;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border: 2.5px solid #1a1a1a !important;
            box-shadow: 4px 4px 0px #1a1a1a !important;
        }

        div[data-testid="stMetric"],
        div[data-testid="metric-container"] {
            border: 2.5px solid #1a1a1a !important;
            background-color: #fffdf5 !important;
            padding: 16px 20px !important;
            border-radius: 18px !important;
            box-shadow: 4px 4px 0px #1a1a1a !important;
        }

        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] * {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-size: 2.4rem !important;
            font-weight: 900 !important;
            color: #1a1a1a !important;
        }

        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] * {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-size: 0.8rem !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
            color: #4b5563 !important;
        }

        div[data-testid="stMetricDelta"] {
            background-color: #fee2e2 !important;
            border: 1.5px solid #991b1b !important;
            border-radius: 20px !important;
            padding: 3px 10px !important;
            display: inline-flex !important;
            align-items: center !important;
            box-shadow: 1.5px 1.5px 0px #1a1a1a !important;
        }

        div[data-testid="stMetricDelta"] svg {
            fill: #991b1b !important;
            color: #991b1b !important;
        }

        div[data-testid="stMetricDelta"] div,
        div[data-testid="stMetricDelta"] span,
        div[data-testid="stMetricDelta"] p {
            color: #991b1b !important;
            font-weight: 800 !important;
            font-size: 0.85rem !important;
        }

        div[data-testid="stDataFrame"] {
            border: 2.5px solid #1a1a1a !important;
            border-radius: 16px !important;
            box-shadow: 4px 4px 0px #1a1a1a !important;
            overflow: hidden !important;
            background-color: #ffffff !important;
            margin-bottom: 18px !important;
        }

        div[data-testid="stHorizontalBlock"] {
            margin-bottom: 24px !important;
        }

        div[data-testid="stTabs"],
        .stTabs {
            margin-top: 28px !important;
            padding-top: 10px !important;
        }

        div[data-testid="stTabs"] [data-baseweb="tab-list"],
        .stTabs [data-baseweb="tab-list"],
        [data-baseweb="tab-list"] {
            margin-top: 20px !important;
            gap: 8px !important;
            border-bottom: 2.5px solid #1a1a1a !important;
            padding-bottom: 4px !important;
            margin-bottom: 22px !important;
        }

        div[data-testid="stTabs"] [data-baseweb="tab"],
        .stTabs [data-baseweb="tab"],
        [data-baseweb="tab"] {
            border-radius: 12px 12px 0px 0px !important;
            border: 2px solid #1a1a1a !important;
            background-color: #ede7dc !important;
            padding: 8px 16px !important;
            margin-right: 4px !important;
        }

        div[data-testid="stTabs"] [data-baseweb="tab"] p,
        div[data-testid="stTabs"] [data-baseweb="tab"] span,
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span,
        [data-baseweb="tab"] p,
        [data-baseweb="tab"] span {
            color: #1a1a1a !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 800 !important;
            font-size: 0.92rem !important;
        }

        div[data-testid="stTabs"] [aria-selected="true"],
        .stTabs [aria-selected="true"],
        [aria-selected="true"][data-baseweb="tab"] {
            background-color: #fffdf5 !important;
            border: 2.5px solid #1a1a1a !important;
            border-bottom: none !important;
            box-shadow: 2.5px -2.5px 0px #1a1a1a !important;
        }

        div[data-testid="stTabs"] [aria-selected="true"] p,
        div[data-testid="stTabs"] [aria-selected="true"] span,
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span,
        [aria-selected="true"][data-baseweb="tab"] p,
        [aria-selected="true"][data-baseweb="tab"] span {
            color: #1a1a1a !important;
            font-weight: 900 !important;
        }

        .stButton > button {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            border: 2.5px solid #1a1a1a !important;
            background-color: #fffdf5 !important;
            color: #1a1a1a !important;
            border-radius: 14px !important;
            box-shadow: 3px 3px 0px #1a1a1a !important;
            padding: 10px 20px !important;
            transition: all 0.1s ease-in-out !important;
        }

        .stButton > button:hover {
            background-color: #fde047 !important;
            color: #1a1a1a !important;
            box-shadow: 1px 1px 0px #1a1a1a !important;
            transform: translate(2px, 2px);
        }

        .stButton > button[kind="primary"] {
            border: 2.5px solid #1a1a1a !important;
            background-color: #f05a50 !important;
            color: #ffffff !important;
            box-shadow: 4px 4px 0px #1a1a1a !important;
        }

        .stButton > button[kind="primary"] * {
            color: #ffffff !important;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: #e0483e !important;
            color: #ffffff !important;
            box-shadow: 1px 1px 0px #1a1a1a !important;
            transform: translate(2px, 2px);
        }
    </style>
    """
    st.markdown(neo_css, unsafe_allow_html=True)


def render_header():
    """
    Renders the dashboard top header with bold Neo-Brutalist card styling, coral badges, and dark shadows.
    Takes no arguments and writes rendered Markdown to the Streamlit page.
    """
    inject_neo_brutalist_styling()
    st.markdown(
        """
        <div style="background-color: #fffdf5; border: 2.5px solid #1a1a1a; border-radius: 20px;
                    padding: 24px; margin-bottom: 24px; box-shadow: 5px 5px 0px #1a1a1a;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="background-color: #f05a50; color: #ffffff; border: 2px solid #1a1a1a;
                             padding: 6px 14px; border-radius: 12px; font-weight: 900; font-size: 0.9rem;
                             box-shadow: 2.5px 2.5px 0px #1a1a1a; letter-spacing: 0.5px;">
                    GMAIL DEFENDER
                </span>
                <span style="border: 2px solid #1a1a1a; background: #ede7dc; padding: 4px 12px;
                             border-radius: 12px; font-weight: 800; font-size: 0.8rem; box-shadow: 2px 2px 0px #1a1a1a; color: #1a1a1a;">
                    ACTIVE PROTECTION
                </span>
            </div>
            <h1 style="margin: 0; font-size: 2.3rem; font-weight: 900; color: #1a1a1a; letter-spacing: -0.5px;">
                Smart Mailbox & Spam Cleaner
            </h1>
            <p style="margin: 6px 0 0 0; color: #475569; font-size: 1rem; font-weight: 600;">
                Machine-learning powered email classification with Scikit-Learn, SQLite audit logging, and one-click Gmail Trash cleanup.
            </p>
            <div style="margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap;">
                <span style="background: #107c41; color: white; border: 2px solid #1a1a1a; padding: 4px 12px; border-radius: 10px; font-size: 0.8rem; font-weight: 800; box-shadow: 2px 2px 0px #1a1a1a;">TF-IDF + Logistic Regression</span>
                <span style="background: #a8e6cf; color: #1a1a1a; border: 2px solid #1a1a1a; padding: 4px 12px; border-radius: 10px; font-size: 0.8rem; font-weight: 800; box-shadow: 2px 2px 0px #1a1a1a;">Google Gmail API</span>
                <span style="background: #e8dfc8; color: #1a1a1a; border: 2px solid #1a1a1a; padding: 4px 12px; border-radius: 10px; font-size: 0.8rem; font-weight: 800; box-shadow: 2px 2px 0px #1a1a1a;">SQLite3 Storage</span>
                <span style="background: #ffd166; color: #1a1a1a; border: 2px solid #1a1a1a; padding: 4px 12px; border-radius: 10px; font-size: 0.8rem; font-weight: 800; box-shadow: 2px 2px 0px #1a1a1a;">Streamlit UI</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_saved_account_config(config_path=".env"):
    """
    Reads saved email address and app password credentials from a local configuration file.
    Takes the configuration file path string and returns a dictionary with email and password strings.
    """
    credentials = {"email": "", "password": ""}
    if not os.path.exists(config_path):
        return credentials

    with open(config_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line.startswith("GMAIL_ADDRESS="):
                credentials["email"] = line.split("=", 1)[1].strip()
            elif line.startswith("GMAIL_APP_PASSWORD="):
                credentials["password"] = line.split("=", 1)[1].strip()

    return credentials


def save_account_config(email_address, app_password, config_path=".env"):
    """
    Persists user Gmail credentials to a local configuration file for automatic future sessions.
    Takes email address, app password, and file path, returning boolean success status.
    """
    content = f"GMAIL_ADDRESS={email_address.strip()}\nGMAIL_APP_PASSWORD={app_password.strip()}\n"
    with open(config_path, "w", encoding="utf-8") as file:
        file.write(content)
    return True


def clear_saved_account_config(config_path=".env"):
    """
    Deletes the saved configuration file to forget stored credentials and reset session state.
    Takes the configuration file path string and returns boolean success status.
    """
    if os.path.exists(config_path):
        os.remove(config_path)
    return True


def handle_credentials_upload(uploaded_file):
    """
    Saves an uploaded OAuth client secrets JSON file to credentials.json in the working directory.
    Takes the Streamlit UploadedFile object and returns boolean success status.
    """
    if uploaded_file is None:
        return False
    with open("credentials.json", "wb") as output_file:
        output_file.write(uploaded_file.getbuffer())
    return True


def render_sidebar_controls():
    """
    Renders sidebar widgets including account connection forms, scan parameters, and system status indicators.
    Takes no arguments and returns a dictionary of configuration settings and connection parameters.
    """
    st.sidebar.markdown(
        """
        <div style="background: #fffdf5; border: 2.5px solid #1a1a1a; border-radius: 16px; padding: 14px;
                    margin-bottom: 16px; box-shadow: 3px 3px 0px #1a1a1a;">
            <h2 style="color: #1a1a1a; margin: 0; font-size: 1.4rem; font-weight: 900;">Connect Mailbox</h2>
            <span style="color: #475569; font-size: 0.8rem; font-weight: 800;">CHOOSE CONNECTION METHOD</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saved_config = load_saved_account_config()
    has_saved_account = bool(saved_config["email"] and saved_config["password"])

    if has_saved_account and "connected_email" not in st.session_state:
        st.session_state["connected_email"] = saved_config["email"]
        st.session_state["app_password"] = saved_config["password"]
        st.session_state["connection_type"] = "IMAP"

    connection_methods = [
        "App Password (16-Digit Code)",
        "1-Click Google Sign-In (No Passwords)",
        "Presentation Demo Mode (Simulation)",
    ]

    default_mode_index = 0
    if os.path.exists("token.json"):
        default_mode_index = 1
    elif has_saved_account:
        default_mode_index = 0

    selected_method = st.sidebar.radio(
        "Connection Type:",
        options=connection_methods,
        index=default_mode_index,
        help="Select App Password for instant connection, or Google Sign-In for OAuth.",
    )

    if selected_method == "App Password (16-Digit Code)":
        default_email = st.session_state.get("connected_email", saved_config.get("email", ""))
        default_pwd = st.session_state.get("app_password", saved_config.get("password", ""))

        user_email = st.sidebar.text_input("Gmail Address", value=default_email, placeholder="yourname@gmail.com")
        user_password = st.sidebar.text_input(
            "16-Character App Password",
            value=default_pwd,
            type="password",
            placeholder="abcd efgh ijkl mnop",
            help="Generate an App Password at myaccount.google.com/apppasswords",
        )

        st.sidebar.markdown(
            """
            <div style="background-color: #fef08a; border: 2px solid #1a1a1a; border-radius: 12px;
                        padding: 10px 14px; margin: 10px 0 14px 0; box-shadow: 3px 3px 0px #1a1a1a;">
                <a href="https://myaccount.google.com/apppasswords" target="_blank"
                   style="color: #1a1a1a !important; text-decoration: none !important; font-weight: 800; font-size: 0.85rem; display: block;">
                    👉 CLICK HERE TO GENERATE PASSWORD ↗
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.sidebar.expander("ℹ️ How to get your 16-Digit Password"):
            st.markdown(
                """
                1. Click the yellow button above to open Google Security.
                2. Make sure **2-Step Verification** is turned ON.
                3. Name the app (e.g. `Spam Cleaner`) and click **Create**.
                4. Google displays a 16-letter code.
                5. Copy and paste it into the box above!
                """
            )

        remember_credentials = st.sidebar.checkbox(
            "💾 Remember credentials on this machine",
            value=True,
            help="Saves your password locally in .env so you do not have to retype it next time.",
        )

        if has_saved_account:
            st.sidebar.caption("✅ Saved account active on this device.")
            if st.sidebar.button("🗑️ Forget Saved Account", use_container_width=True):
                clear_saved_account_config()
                st.session_state.pop("connected_email", None)
                st.session_state.pop("app_password", None)
                st.session_state["connection_type"] = "DEMO"
                st.rerun()

        if st.sidebar.button("🔗 Connect Gmail Account", type="primary", use_container_width=True):
            if not user_email or not user_password:
                st.sidebar.error("Please enter both Gmail address and 16-character App Password.")
            else:
                with st.sidebar.spinner("Connecting to Gmail IMAP..."):
                    success, message = gmail_service.test_imap_connection(user_email, user_password)
                    if success:
                        st.session_state["connected_email"] = user_email.strip()
                        st.session_state["app_password"] = user_password.strip()
                        st.session_state["connection_type"] = "IMAP"
                        if remember_credentials:
                            save_account_config(user_email, user_password)
                        st.sidebar.success(f"Connected to {user_email.strip()}!")
                        st.rerun()
                    else:
                        st.sidebar.markdown(
                            f"""
                            <div style="background-color: #fee2e2; border: 2.5px solid #1a1a1a; border-radius: 14px;
                                        padding: 12px 14px; box-shadow: 3px 3px 0px #1a1a1a; margin-top: 10px;">
                                <div style="font-weight: 800; color: #991b1b; font-size: 0.9rem; margin-bottom: 4px;">
                                    ⚠️ Connection Failed
                                </div>
                                <div style="font-weight: 600; color: #1a1a1a; font-size: 0.82rem; line-height: 1.4;">
                                    {message}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    elif selected_method == "1-Click Google Sign-In (No Passwords)":
        credentials_exist = os.path.exists("credentials.json")
        token_exist = os.path.exists("token.json")

        if not credentials_exist:
            st.sidebar.info("Set up Google OAuth once:")
            uploaded_file = st.sidebar.file_uploader("Upload credentials.json", type=["json"])
            if uploaded_file and handle_credentials_upload(uploaded_file):
                st.sidebar.success("credentials.json uploaded!")
                st.rerun()

            with st.sidebar.expander("Or Paste Google Client ID & Secret"):
                raw_client_id = st.text_input("Client ID", placeholder="xxxx.apps.googleusercontent.com")
                raw_client_secret = st.text_input("Client Secret", type="password")
                if st.button("💾 Save Google OAuth Keys"):
                    if raw_client_id and raw_client_secret:
                        gmail_service.create_credentials_file_from_keys(raw_client_id, raw_client_secret)
                        st.sidebar.success("Saved credentials.json!")
                        st.rerun()

        if credentials_exist:
            if token_exist:
                st.sidebar.success("Google OAuth: Active & Connected")
                st.session_state["connection_type"] = "OAUTH"
                if "connected_email" not in st.session_state:
                    st.session_state["connected_email"] = "Authorized Google User"

                if st.sidebar.button("🔄 Switch Account", use_container_width=True):
                    if os.path.exists("token.json"):
                        os.remove("token.json")
                    st.session_state.pop("connected_email", None)
                    st.rerun()
            else:
                user_hint = st.sidebar.text_input("Your Gmail Address (Optional)", placeholder="yourname@gmail.com")
                if st.sidebar.button("🔐 Sign In with Google", type="primary", use_container_width=True):
                    with st.sidebar.spinner("Opening Google Sign-In window in your browser..."):
                        try:
                            client = gmail_service.get_gmail_service(login_hint=user_hint)
                            st.session_state["gmail_client"] = client
                            st.session_state["connected_email"] = user_hint or "Authorized Google User"
                            st.session_state["connection_type"] = "OAUTH"
                            st.sidebar.success("Successfully signed in with Google!")
                            st.rerun()
                        except Exception as error:
                            st.sidebar.error(f"Sign-in failed: {error}")

    else:
        st.session_state["connection_type"] = "DEMO"
        st.session_state["connected_email"] = "Demo Simulation (10 Synthetic Emails)"
        st.sidebar.warning("⚠️ Simulation mode active. Real Gmail is NOT connected.")

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="background: #fffdf5; border: 2.5px solid #1a1a1a; border-radius: 16px; padding: 14px;
                    margin-bottom: 14px; box-shadow: 3px 3px 0px #1a1a1a;">
            <h3 style="color: #1a1a1a; margin: 0; font-size: 1.2rem; font-weight: 900;">Scan Settings</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    scan_limit = st.sidebar.slider("Number of Emails to Scan", min_value=5, max_value=50, value=10, step=5)
    spam_threshold = st.sidebar.slider("Spam Probability Threshold", min_value=0.10, max_value=0.95, value=0.50, step=0.05)

    return {
        "selected_method": selected_method,
        "connected_email": st.session_state.get("connected_email", "Demo Simulation (10 Synthetic Emails)"),
        "connection_type": st.session_state.get("connection_type", "DEMO"),
        "scan_limit": scan_limit,
        "spam_threshold": spam_threshold,
    }


def render_summary_metrics(statistics):
    """
    Renders high-level presentation KPI cards displaying aggregate counts from the SQLite database.
    Takes a dictionary containing total_scanned, total_spam, total_ham, and total_trashed, returning None.
    """
    column1, column2, column3, column4 = st.columns(4)

    total_scanned = statistics.get("total_scanned", 0)
    total_spam = statistics.get("total_spam", 0)
    total_ham = statistics.get("total_ham", 0)
    total_trashed = statistics.get("total_trashed", 0)

    spam_rate = (total_spam / total_scanned * 100) if total_scanned > 0 else 0.0

    column1.metric("Total Scanned", f"{total_scanned:,}")
    column2.metric("Detected Spam", f"{total_spam:,}", delta=f"{spam_rate:.1f}% rate", delta_color="inverse")
    column3.metric("Verified Ham", f"{total_ham:,}")
    column4.metric("Moved to Trash", f"{total_trashed:,}")


def execute_move_to_trash(target_ids, connection_type):
    """
    Dispatches trash request to appropriate backend (IMAP, Gmail API, or Demo) and updates database.
    Takes list of target message IDs and string connection type, returning count of trashed messages.
    """
    if not target_ids:
        return 0

    if connection_type == "IMAP":
        user_email = st.session_state.get("connected_email", "")
        app_password = st.session_state.get("app_password", "")
        gmail_service.move_emails_to_trash_imap(user_email, app_password, target_ids)
    elif connection_type == "OAUTH":
        gmail_client = gmail_service.get_gmail_service()
        gmail_service.move_emails_to_trash_batch(gmail_client, target_ids)

    database.update_emails_status_batch(target_ids, new_status="TRASHED")
    return len(target_ids)


def render_spam_action_panel(spam_emails, connection_type):
    """
    Renders detected spam inspection panel with individual selection checkboxes and move-to-trash buttons.
    Takes list of spam email dictionaries and string connection type, writing interactive components to page.
    """
    active_spam = [item for item in spam_emails if item.get("status") != "TRASHED"]

    if not active_spam:
        st.markdown(
            """
            <div style="background-color: #dcfce7; border: 2.5px solid #1a1a1a; border-radius: 16px;
                        padding: 16px 20px; box-shadow: 4px 4px 0px #1a1a1a; margin-bottom: 16px;
                        display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 1.5rem;">🎉</span>
                <span style="color: #1a1a1a; font-weight: 800; font-size: 1.05rem;">
                    No active spam detected in this scan! Your inbox looks clean.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div style="background-color: #fee2e2; border: 2.5px solid #1a1a1a; padding: 14px 20px;
                    border-radius: 16px; margin-bottom: 16px; box-shadow: 4px 4px 0px #1a1a1a;">
            <span style="color: #991b1b; font-size: 1.15rem; font-weight: 800;">
                ⚠️ {len(active_spam)} Spam Email(s) Detected & Ready for Cleanup
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_ids = []
    action_col1, action_col2 = st.columns([2.5, 1.5])

    with action_col2:
        move_all_button = st.button("🗑️ Move ALL Detected Spam to Trash", type="primary", use_container_width=True)

    with action_col1:
        st.markdown(
            "Select individual messages below or use the bulk red action button to clean your mailbox:"
        )

    for item in active_spam:
        prob = item.get("spam_probability", 0.0) * 100
        msg_id = item.get("message_id", "")
        subject = item.get("subject", "(No Subject)")
        sender = item.get("sender", "(Unknown)")
        date_str = item.get("date_received", "")
        snippet = item.get("snippet", "")

        box_col1, box_col2 = st.columns([0.05, 0.95])
        with box_col1:
            checked = st.checkbox("", key=f"select_{msg_id}")
            if checked:
                selected_ids.append(msg_id)

        with box_col2:
            with st.expander(f"🚨 [{prob:.1f}% Spam] {subject} — from: {sender}", expanded=True):
                st.markdown(f"**Sender:** `{sender}` | **Date:** `{date_str}` | **ID:** `{msg_id}`")
                st.markdown(f"**Snippet:** {snippet}")
                st.progress(min(prob / 100.0, 1.0))
                if item.get("body"):
                    st.text_area("Email Content Preview", item.get("body"), height=90, key=f"preview_{msg_id}", disabled=True)

    target_ids_to_trash = []
    if move_all_button:
        target_ids_to_trash = [item["message_id"] for item in active_spam]
    elif st.button("🗑️ Move Selected Spam to Trash", disabled=len(selected_ids) == 0):
        target_ids_to_trash = selected_ids

    if target_ids_to_trash:
        with st.spinner("Moving spam emails to Gmail Trash and updating database..."):
            try:
                count = execute_move_to_trash(target_ids_to_trash, connection_type)
                if connection_type == "DEMO":
                    st.info(
                        f"ℹ️ [DEMO SIMULATION] Marked {count} synthetic test emails as TRASHED in SQLite. "
                        "Connect your real Gmail in the sidebar to delete real emails from mail.google.com."
                    )
                else:
                    st.success(
                        f"✅ Successfully moved {count} email(s) directly into your REAL Gmail Trash! "
                        "Open mail.google.com -> Trash to see them."
                    )
                st.rerun()
            except Exception as error:
                st.error(f"Failed to move emails to Trash: {error}")


def render_scan_results_tab(classified_emails):
    """
    Renders detailed presentation cards for all emails retrieved in the most recent scan session.
    Takes a list of classified email record dictionaries and writes structured UI cards.
    """
    if not classified_emails:
        st.info("No emails scanned in this session yet. Click '🚀 Scan Inbox Now' above.")
        return

    st.subheader(f"Latest Scan Feed ({len(classified_emails)} Emails)")

    for email in classified_emails:
        is_spam = email.get("is_spam", 0) == 1
        probability = email.get("spam_probability", 0.0) * 100
        status = email.get("status", "INBOX")

        badge_bg = "#f05a50" if is_spam else "#a8e6cf"
        badge_text_color = "#ffffff" if is_spam else "#1a1a1a"
        badge_text = f"-{probability:.0f}% SPAM" if is_spam else f"HAM ({100 - probability:.0f}%)"

        st.markdown(
            f"""
            <div style="background-color: #fffdf5; border: 2.5px solid #1a1a1a; border-radius: 18px;
                        padding: 16px 20px; margin-bottom: 14px; box-shadow: 4px 4px 0px #1a1a1a;
                        display: flex; justify-content: space-between; align-items: flex-start; gap: 16px;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                        <span style="background-color: {badge_bg}; color: {badge_text_color}; border: 1.5px solid #1a1a1a;
                                     padding: 3px 10px; border-radius: 10px; font-weight: 800; font-size: 0.75rem;
                                     box-shadow: 1.5px 1.5px 0px #1a1a1a;">
                            {badge_text}
                        </span>
                        <span style="background-color: #1a1a1a; color: #ffffff; padding: 2px 8px; border-radius: 6px;
                                     font-weight: 800; font-size: 0.7rem; text-transform: uppercase;">
                            {email.get('sender', '')[:28]}
                        </span>
                    </div>
                    <div style="font-weight: 800; font-size: 1.15rem; color: #1a1a1a; margin-bottom: 4px;">
                        {email.get('subject', '(No Subject)')}
                    </div>
                    <div style="color: #475569; font-size: 0.88rem; font-weight: 600;">
                        {email.get('snippet', '')}
                    </div>
                </div>
                <div style="text-align: right; min-width: 90px;">
                    <div style="font-weight: 900; font-size: 1.35rem; color: #1a1a1a;">
                        {probability:.1f}%
                    </div>
                    <div style="font-size: 0.72rem; color: #64748b; font-weight: 800; text-transform: uppercase;">
                        {status}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_history_tab():
    """
    Renders the persistent SQLite scan history table with search filtering and CSV export capability.
    Takes no inputs, queries database directly, and writes an interactive table to the page.
    """
    st.subheader("📜 SQLite Scan History (emails.db)")
    history_records = database.fetch_scan_history(limit=200)

    if not history_records:
        st.info("No scan history found in SQLite database yet. Run a scan to populate records.")
        return

    history_dataframe = pd.DataFrame(history_records)
    display_columns = [
        "message_id",
        "subject",
        "sender",
        "date_received",
        "spam_probability",
        "is_spam",
        "status",
        "scanned_at",
    ]
    available_columns = [col for col in display_columns if col in history_dataframe.columns]
    filtered_dataframe = history_dataframe[available_columns]

    st.dataframe(
        filtered_dataframe,
        use_container_width=True,
        column_config={
            "spam_probability": st.column_config.ProgressColumn(
                "Spam Probability",
                help="Predicted probability of the email being spam",
                format="%.2f",
                min_value=0.0,
                max_value=1.0,
            ),
            "is_spam": st.column_config.CheckboxColumn("Is Spam?"),
        },
    )

    csv_data = filtered_dataframe.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Scan History as CSV",
        data=csv_data,
        file_name="scanned_emails_history.csv",
        mime="text/csv",
    )


def render_interactive_test_tab(model_pipeline, threshold):
    """
    Renders an interactive real-time classifier testing form for live audience demonstrations.
    Takes the Scikit-Learn model pipeline and float classification threshold, returning None.
    """
    st.subheader("🧪 Live Presentation Email Tester")
    st.markdown(
        "Type or paste any custom email subject and body below to test the trained Scikit-Learn pipeline in real time:"
    )

    sample_buttons_col1, sample_buttons_col2, sample_buttons_col3 = st.columns(3)
    default_subject = "Urgent: Verify your account immediately"
    default_body = "Your account has been temporarily locked due to suspicious activity. Click here to confirm your password and avoid termination."

    if sample_buttons_col1.button("📋 Load Phishing Sample"):
        st.session_state["test_subject"] = "Urgent: Verify your account immediately"
        st.session_state["test_body"] = "Your account has been temporarily locked due to suspicious activity. Click here to confirm your password and avoid termination."
    elif sample_buttons_col2.button("📋 Load Lottery Scam Sample"):
        st.session_state["test_subject"] = "Congratulations! You have won $1,000,000"
        st.session_state["test_body"] = "You were selected as the official winner in our sweepstakes. Send your bank details and passport copy to claim your prize."
    elif sample_buttons_col3.button("📋 Load Legitimate Team Sample"):
        st.session_state["test_subject"] = "Sprint planning notes & PR review"
        st.session_state["test_body"] = "Hi team, please find attached the meeting notes from today's sync. Let me know if you can review PR #42 before lunch."

    input_subject = st.text_input(
        "Email Subject",
        value=st.session_state.get("test_subject", default_subject),
        key="input_subject",
    )
    input_body = st.text_area(
        "Email Body",
        value=st.session_state.get("test_body", default_body),
        height=140,
        key="input_body",
    )

    if st.button("🔍 Classify Test Email", type="primary"):
        combined_text = f"{input_subject} {input_body}".strip()
        if not combined_text:
            st.warning("Please enter email text to evaluate.")
            return

        probabilities = model_pipeline.predict_proba([combined_text])[0]
        spam_probability = float(probabilities[1])
        ham_probability = float(probabilities[0])
        is_spam = spam_probability >= threshold

        result_col1, result_col2 = st.columns(2)
        with result_col1:
            if is_spam:
                st.error(f"🚨 **Result: SPAM DETECTED** ({spam_probability * 100:.2f}% confidence)")
            else:
                st.success(f"✅ **Result: LEGITIMATE (HAM)** ({ham_probability * 100:.2f}% confidence)")

        with result_col2:
            st.metric("Spam Probability", f"{spam_probability * 100:.2f}%")
            st.progress(min(spam_probability, 1.0))


def execute_scan(scan_limit, spam_threshold, connection_type, model_pipeline):
    """
    Executes the scan workflow by fetching emails, predicting spam probabilities, and logging to SQLite.
    Takes scan limit, probability threshold, connection type string, and model pipeline, returning email records.
    """
    raw_emails = []

    if connection_type == "IMAP":
        user_email = st.session_state.get("connected_email", "")
        app_password = st.session_state.get("app_password", "")
        if not user_email or not app_password:
            st.error("Please connect your Gmail account in the sidebar first.")
            return []
        try:
            raw_emails = gmail_service.fetch_inbox_emails_imap(user_email, app_password, max_results=scan_limit)
        except Exception as error:
            st.error(f"IMAP Fetch Error: {error}")
            return []

    elif connection_type == "OAUTH":
        try:
            gmail_client = gmail_service.get_gmail_service()
            raw_emails = gmail_service.fetch_inbox_emails(gmail_client, max_results=scan_limit)
        except Exception as error:
            st.error(f"OAuth Fetch Error: {error}")
            return []

    else:
        raw_emails = gmail_service.get_sample_demo_emails(count=scan_limit)

    if not raw_emails:
        st.warning("No emails retrieved from the mailbox.")
        return []

    classified_emails = classify_emails(model_pipeline, raw_emails, threshold=spam_threshold)
    database.insert_scanned_emails_batch(classified_emails)
    return classified_emails


def main():
    """
    Main orchestration routine coordinating database initialization, sidebar inputs, scan workflows, and UI tabs.
    Takes no inputs and manages Streamlit state and visual component rendering.
    """
    database.initialize_database()
    render_header()

    controls = render_sidebar_controls()
    model_pipeline = load_spam_model()

    if not model_pipeline:
        st.error("⚠️ Trained ML model pipeline (`spam_model.joblib`) not found.")
        if st.button("🚀 Train Model Now (`train_model.py`)", type="primary"):
            with st.spinner("Training model with TF-IDF Vectorizer + Logistic Regression..."):
                import train_model

                train_model.train_model()
                st.cache_resource.clear()
                st.success("Model trained and saved successfully!")
                st.rerun()
        return

    statistics = database.fetch_email_statistics()
    render_summary_metrics(statistics)

    st.markdown("<hr style='border: 1.5px solid #1a1a1a; margin: 24px 0;'>", unsafe_allow_html=True)

    active_email = controls["connected_email"]
    action_bar_col1, action_bar_col2 = st.columns([2.2, 1.2])

    with action_bar_col1:
        if controls["connection_type"] == "DEMO":
            st.markdown(
                """
                <div style="background-color: #fef08a; border: 2.5px solid #1a1a1a; border-radius: 14px;
                            padding: 12px 18px; box-shadow: 3.5px 3.5px 0px #1a1a1a; display: flex; align-items: center; gap: 10px; margin-bottom: 18px;">
                    <span style="font-size: 1.2rem;">⚠️</span>
                    <span style="color: #1a1a1a; font-weight: 800; font-size: 0.95rem;">
                        Simulation mode active. Real Gmail is NOT connected.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif controls["connection_type"] == "OAUTH":
            st.markdown(
                f"""
                <div style="background-color: #bbf7d0; border: 2.5px solid #1a1a1a; border-radius: 14px;
                            padding: 12px 18px; box-shadow: 3.5px 3.5px 0px #1a1a1a; display: flex; align-items: center; gap: 10px; margin-bottom: 18px;">
                    <span style="font-size: 1.2rem;">🟢</span>
                    <span style="color: #1a1a1a; font-weight: 800; font-size: 0.95rem;">
                        Google OAuth Active: Connected to real Gmail ({active_email}).
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background-color: #bbf7d0; border: 2.5px solid #1a1a1a; border-radius: 14px;
                            padding: 12px 18px; box-shadow: 3.5px 3.5px 0px #1a1a1a; display: flex; align-items: center; gap: 10px; margin-bottom: 18px;">
                    <span style="font-size: 1.2rem;">🟢</span>
                    <span style="color: #1a1a1a; font-weight: 800; font-size: 0.95rem;">
                        IMAP Active: Connected to real Gmail ({active_email}).
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with action_bar_col2:
        if st.button("🚀 Scan Inbox Now", type="primary", use_container_width=True):
            with st.spinner(f"Scanning inbox for {active_email}..."):
                scanned_results = execute_scan(
                    controls["scan_limit"],
                    controls["spam_threshold"],
                    controls["connection_type"],
                    model_pipeline,
                )
                st.session_state["latest_scan"] = scanned_results
                st.rerun()

    st.markdown("<div style='height: 24px; width: 100%; display: block;'>&nbsp;</div>", unsafe_allow_html=True)
    latest_emails = st.session_state.get("latest_scan", [])
    detected_spam_emails = [email for email in latest_emails if email.get("is_spam") == 1]

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            f"🚨 Detected Spam ({len(detected_spam_emails)})",
            f"📬 Latest Scan Feed ({len(latest_emails)})",
            "📜 SQLite History Log",
            "🧪 Live Model Sandbox",
        ]
    )

    with tab1:
        render_spam_action_panel(detected_spam_emails, controls["connection_type"])

    with tab2:
        render_scan_results_tab(latest_emails)

    with tab3:
        render_history_tab()

    with tab4:
        render_interactive_test_tab(model_pipeline, controls["spam_threshold"])


if __name__ == "__main__":
    main()
