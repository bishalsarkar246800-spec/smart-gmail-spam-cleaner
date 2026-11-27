import base64
import email
from email.header import decode_header
import imaplib
import json
import os
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    InstalledAppFlow = None

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def create_credentials_file_from_keys(client_id, client_secret, output_path="credentials.json"):
    """
    Generates a valid Google OAuth client secrets JSON file from raw client ID and secret strings.
    Takes client ID string, client secret string, and destination path, returning boolean success.
    """
    oauth_structure = {
        "installed": {
            "client_id": client_id.strip(),
            "client_secret": client_secret.strip(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(oauth_structure, file, indent=2)
    try:
        os.chmod(output_path, 0o600)
    except OSError:
        pass
    return True


def get_gmail_service(credentials_path="credentials.json", token_path="token.json", login_hint=None):
    """
    Authenticates with Google Cloud OAuth 2.0 with gmail.modify scope and initializes the Gmail API client.
    Takes paths to credentials.json, token.json, and optional login_hint, returning an authorized Resource client.
    """
    if InstalledAppFlow is None:
        raise ImportError(
            "The 'google-auth-oauthlib' package is required for live Gmail authentication. "
            "Please install it using 'pip install google-auth-oauthlib'."
        )

    credentials = None

    if os.path.exists(token_path):
        credentials = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"OAuth client file '{credentials_path}' was not found. "
                    "Please download client secrets from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            server_kwargs = {"port": 0}
            if login_hint:
                server_kwargs["login_hint"] = login_hint
            credentials = flow.run_local_server(**server_kwargs)

        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(credentials.to_json())
        try:
            os.chmod(token_path, 0o600)
        except OSError:
            pass

    return build("gmail", "v1", credentials=credentials)


def decode_base64_data(encoded_data):
    """
    Decodes a base64url-encoded string from Gmail API into UTF-8 text.
    Takes a base64url string and returns the decoded plain text string.
    """
    if not encoded_data:
        return ""
    decoded_bytes = base64.urlsafe_b64decode(encoded_data.encode("utf-8"))
    return decoded_bytes.decode("utf-8", errors="replace")


def extract_email_header(headers, target_header_name):
    """
    Searches a list of Gmail message header dictionaries to find the value for a given field name.
    Takes a list of header dictionaries and the case-insensitive header name, returning the matched string value.
    """
    normalized_target = target_header_name.lower()
    for header in headers:
        if header.get("name", "").lower() == normalized_target:
            return header.get("value", "")
    return ""


def extract_plain_text_from_payload(payload):
    """
    Traverses the Gmail message payload structure recursively to locate and decode the plain-text body.
    Takes a Gmail message payload dictionary and returns the decoded plain-text content string.
    """
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return decode_base64_data(body_data)

    parts = payload.get("parts", [])
    for part in parts:
        part_mime = part.get("mimeType", "")
        part_body_data = part.get("body", {}).get("data", "")
        if part_mime == "text/plain" and part_body_data:
            return decode_base64_data(part_body_data)

    for part in parts:
        if "parts" in part:
            extracted_text = extract_plain_text_from_payload(part)
            if extracted_text:
                return extracted_text

    if mime_type == "text/html" and body_data:
        raw_html = decode_base64_data(body_data)
        clean_text = re.sub(r"<[^>]+>", " ", raw_html)
        return re.sub(r"\s+", " ", clean_text).strip()

    return ""


def fetch_inbox_emails(gmail_service, max_results=10):
    """
    Fetches latest inbox messages, retrieves full metadata, and parses headers and plain text bodies.
    Takes an authorized Gmail service and integer limit, returning a list of parsed email dictionaries.
    """
    response = (
        gmail_service.users()
        .messages()
        .list(userId="me", q="in:inbox", maxResults=max_results)
        .execute()
    )

    messages = response.get("messages", [])
    parsed_emails = []

    for message_item in messages:
        message_id = message_item["id"]
        full_message = (
            gmail_service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        payload = full_message.get("payload", {})
        headers = payload.get("headers", [])

        subject = extract_email_header(headers, "Subject") or "(No Subject)"
        sender = extract_email_header(headers, "From") or "(Unknown Sender)"
        date_received = extract_email_header(headers, "Date") or ""
        snippet = full_message.get("snippet", "")
        body_text = extract_plain_text_from_payload(payload) or snippet

        parsed_emails.append(
            {
                "message_id": message_id,
                "subject": subject,
                "sender": sender,
                "date_received": date_received,
                "snippet": snippet,
                "body": body_text,
                "status": "INBOX",
            }
        )

    return parsed_emails


def move_email_to_trash(gmail_service, message_id):
    """
    Moves an individual message to the Gmail Trash using the messages.trash endpoint.
    Takes an authorized Gmail service and target message ID string, returning the API response dictionary.
    """
    return (
        gmail_service.users()
        .messages()
        .trash(userId="me", id=message_id)
        .execute()
    )


def move_emails_to_trash_batch(gmail_service, message_ids):
    """
    Trashes a collection of Gmail messages by iterating through the provided message IDs.
    Takes an authorized Gmail service and list of message IDs, returning a list of successfully trashed IDs.
    """
    trashed_ids = []
    for message_id in message_ids:
        move_email_to_trash(gmail_service, message_id)
        trashed_ids.append(message_id)
    return trashed_ids


def decode_header_string(header_value):
    """
    Decodes RFC 2047 encoded email headers into clean unicode strings.
    Takes raw header string or bytes and returns decoded unicode string.
    """
    if not header_value:
        return ""
    decoded_fragments = decode_header(header_value)
    text_segments = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            charset = encoding or "utf-8"
            try:
                text_segments.append(fragment.decode(charset, errors="replace"))
            except LookupError:
                text_segments.append(fragment.decode("utf-8", errors="replace"))
        else:
            text_segments.append(str(fragment))
    return "".join(text_segments)


def extract_body_from_email_message(email_message):
    """
    Traverses an email.message.Message structure to extract and clean the plain-text body.
    Takes a parsed EmailMessage instance and returns a cleaned body string.
    """
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in disposition:
                payload_bytes = part.get_payload(decode=True)
                if payload_bytes:
                    return payload_bytes.decode("utf-8", errors="replace")
        for part in email_message.walk():
            content_type = part.get_content_type()
            if content_type == "text/html":
                payload_bytes = part.get_payload(decode=True)
                if payload_bytes:
                    raw_html = payload_bytes.decode("utf-8", errors="replace")
                    clean_text = re.sub(r"<[^>]+>", " ", raw_html)
                    return re.sub(r"\s+", " ", clean_text).strip()
    else:
        payload_bytes = email_message.get_payload(decode=True)
        if payload_bytes:
            return payload_bytes.decode("utf-8", errors="replace")

    return ""


def test_imap_connection(email_address, app_password):
    """
    Validates user credentials against Gmail IMAP SSL server with formatted error diagnostics.
    Takes email address and app password strings, returning a tuple of boolean success and error message.
    """
    clean_email = email_address.strip()
    clean_password = app_password.replace(" ", "").strip()
    if "\r" in clean_email or "\n" in clean_email or "\r" in clean_password or "\n" in clean_password:
        return False, "Security Error: Line break characters are not permitted in credentials."
    if not clean_email or not clean_password:
        return False, "Error: Both email address and app password are required."
    try:
        mail_client = imaplib.IMAP4_SSL("imap.gmail.com")
        mail_client.login(clean_email, clean_password)
        mail_client.logout()
        return True, "Successfully authenticated with Gmail!"
    except Exception as error:
        error_message = str(error)
        if "nodename nor servname" in error_message or "Errno 8" in error_message:
            return (
                False,
                "No Internet Connection: DNS could not reach imap.gmail.com. "
                "Please verify your Wi-Fi or mobile hotspot. "
                "If presenting offline, switch to 'Presentation Demo Mode' in the sidebar."
            )
        if "AUTHENTICATIONFAILED" in error_message:
            return (
                False,
                "Authentication Failed: Invalid email address or 16-character App Password. "
                "Ensure 2-Step Verification is active and generate a fresh password."
            )
        return False, error_message


def find_gmail_trash_folder(mail_client):
    """
    Discovers the exact Trash or Bin folder name on Gmail IMAP server by inspecting SPECIAL-USE attributes.
    Takes an active IMAP client connection and returns the discovered Trash folder string.
    """
    status, folder_list = mail_client.list()
    if status == "OK" and folder_list:
        for folder_bytes in folder_list:
            folder_str = folder_bytes.decode("utf-8", errors="replace")
            if "\\Trash" in folder_str or "\\Bin" in folder_str:
                parts = folder_str.split(' "/" ')
                if len(parts) > 1:
                    raw_name = parts[-1].strip().strip('"')
                    return f'"{raw_name}"'

    candidate_folders = [
        '"[Gmail]/Trash"',
        '"[Gmail]/Bin"',
        '"[Google Mail]/Trash"',
        '"[Google Mail]/Bin"',
        '"Trash"',
        '"Bin"',
    ]
    for candidate in candidate_folders:
        select_status, _ = mail_client.select(candidate, readonly=True)
        if select_status == "OK":
            mail_client.select("INBOX")
            return candidate

    return '"[Gmail]/Trash"'


def fetch_inbox_emails_imap(email_address, app_password, max_results=10):
    """
    Connects to Gmail via IMAP SSL, retrieves latest inbox messages, and parses metadata and body.
    Takes email address, app password, and integer count, returning a list of parsed email dictionaries.
    """
    clean_email = email_address.strip()
    clean_password = app_password.replace(" ", "").strip()
    if "\r" in clean_email or "\n" in clean_email or "\r" in clean_password or "\n" in clean_password:
        raise ValueError("Invalid line break characters detected in credentials.")

    safe_max = max(1, min(int(max_results), 100))
    mail_client = imaplib.IMAP4_SSL("imap.gmail.com")
    mail_client.login(clean_email, clean_password)
    mail_client.select("INBOX")

    status, search_data = mail_client.uid("search", None, "ALL")
    if status != "OK" or not search_data or not search_data[0]:
        mail_client.logout()
        return []

    valid_uids = [uid for uid in search_data[0].split() if uid.decode("utf-8", errors="ignore").isdigit()]
    selected_uids = valid_uids[-safe_max:]
    selected_uids.reverse()

    parsed_emails = []
    for uid_bytes in selected_uids:
        uid_str = uid_bytes.decode("utf-8")
        status, message_data = mail_client.uid("fetch", uid_bytes, "(RFC822)")
        if status != "OK" or not message_data or not message_data[0]:
            continue

        raw_email_bytes = message_data[0][1]
        email_message = email.message_from_bytes(raw_email_bytes)

        subject = decode_header_string(email_message.get("Subject", "(No Subject)"))
        sender = decode_header_string(email_message.get("From", "(Unknown Sender)"))
        date_received = email_message.get("Date", "")
        body_text = extract_body_from_email_message(email_message)
        snippet = (body_text[:160] + "...") if len(body_text) > 160 else body_text

        parsed_emails.append(
            {
                "message_id": f"imap_{uid_str}",
                "subject": subject,
                "sender": sender,
                "date_received": date_received,
                "snippet": snippet,
                "body": body_text,
                "status": "INBOX",
            }
        )

    mail_client.close()
    mail_client.logout()
    return parsed_emails


def move_emails_to_trash_imap(email_address, app_password, message_ids):
    """
    Moves specified emails to Gmail Trash using IMAP Special-Use folder detection, COPY, and flags.
    Takes email address, app password, and list of message ID strings, returning a list of trashed IDs.
    """
    clean_email = email_address.strip()
    clean_password = app_password.replace(" ", "").strip()
    if "\r" in clean_email or "\n" in clean_email or "\r" in clean_password or "\n" in clean_password:
        raise ValueError("Invalid line break characters detected in credentials.")

    mail_client = imaplib.IMAP4_SSL("imap.gmail.com")
    mail_client.login(clean_email, clean_password)
    mail_client.select("INBOX")

    trash_folder = find_gmail_trash_folder(mail_client)
    trashed_ids = []

    for msg_id in message_ids:
        raw_uid = msg_id.replace("imap_", "").strip()
        if not raw_uid.isdigit():
            continue

        copy_status, _ = mail_client.uid("COPY", raw_uid, trash_folder)
        if copy_status != "OK":
            mail_client.uid("MOVE", raw_uid, trash_folder)

        mail_client.uid("STORE", raw_uid, "+FLAGS", "(\\Deleted)")
        mail_client.uid("STORE", raw_uid, "+X-GM-LABELS", "(\\Trash)")
        trashed_ids.append(msg_id)

    mail_client.expunge()
    mail_client.close()
    mail_client.logout()
    return trashed_ids


def get_sample_demo_emails(count=10):
    """
    Generates synthetic presentation-ready email records for testing when Gmail credentials are not active.
    Takes an integer count of emails to generate and returns a list of simulated email dictionaries.
    """
    sample_pool = [
        {
            "message_id": "demo_msg_001",
            "subject": "URGENT: Verify your bank account credentials immediately",
            "sender": "security-alert@bank-verification-portal.com",
            "date_received": "Fri, 21 Nov 2026 10:15:00 +0000",
            "snippet": "Unusual login activity detected from unfamiliar device. Click here to confirm identity.",
            "body": "Dear customer, your bank account access will be terminated within 24 hours unless you verify your password and identity here: http://secure-bank-login.com",
            "status": "INBOX",
        },
        {
            "message_id": "demo_msg_002",
            "subject": "Sprint Retrospective and Planning Agenda",
            "sender": "sarah.lead@company.internal",
            "date_received": "Fri, 21 Nov 2026 09:30:00 +0000",
            "snippet": "Hi team, please find the agenda for today's bi-weekly sprint planning meeting.",
            "body": "Hi team, let us review the completed milestones from sprint 4 and allocate tickets for sprint 5 during our standup at 2 PM.",
            "status": "INBOX",
        },
        {
            "message_id": "demo_msg_003",
            "subject": "YOU WON! Claim your $1,000,000 cash lottery prize now",
            "sender": "claims-agent@international-lottery-winner.org",
            "date_received": "Fri, 21 Nov 2026 08:45:00 +0000",
            "snippet": "Official notification of sweepstakes prize award. Reply with bank account info.",
            "body": "Congratulations lucky winner! Your email address was selected for the annual $1,000,000 cash prize. Send your full name and bank account details.",
            "status": "INBOX",
        },
        {
            "message_id": "demo_msg_004",
            "subject": "Code Review Request: Fix SQLite connection pooling in database.py",
            "sender": "alex.dev@github-updates.com",
            "date_received": "Thu, 20 Nov 2026 18:20:00 +0000",
            "snippet": "Pull request #58 is ready for your review on the main repository branch.",
            "body": "Hey, could you please take a look at pull request #58? I refactored the database connection handler to use context managers properly.",
            "status": "INBOX",
        },
        {
            "message_id": "demo_msg_005",
            "subject": "Exclusive 0% interest loan up to $50,000 approved",
            "sender": "fast-cash@unsecured-instant-loans.net",
            "date_received": "Thu, 20 Nov 2026 16:10:00 +0000",
            "snippet": "Instant disbursement without credit verification. Apply in under 2 minutes.",
            "body": "Pre-approved personal loan offer. Get up to $50,000 deposited into your bank account today. No collateral and no credit check required.",
            "status": "INBOX",
        },
        {
            "message_id": "demo_msg_006",
            "subject": "Amazon Order #402-9812 has shipped",
            "sender": "auto-confirm@amazon.com",
            "date_received": "Thu, 20 Nov 2026 14:05:00 +0000",
            "snippet": "Your package containing 'Mechanical Keyboard' is on the way. Delivery expected tomorrow.",
            "body": "Great news! Your package has been dispatched via UPS. You can track your shipment and view your delivery updates using the link below.",
            "status": "INBOX",
        },
        {
            "message_id": "demo_msg_007",
            "subject": "Action Required: Your PayPal account has been restricted",
            "sender": "service-notice@paypal-resolution-center.biz",
            "date_received": "Thu, 20 Nov 2026 11:50:00 +0000",
            "snippet": "We noticed suspicious checkout attempts. Confirm your credit card to restore access.",
            "body": "Your PayPal account access has been limited. To restore full functionality, please confirm your identity and billing details immediately.",
            "status": "INBOX",
        },
        {
            "message_id": "demo_msg_008",
            "subject": "CSE Project Submission Deadline Reminder",
            "sender": "prof.johnson@university.edu",
            "date_received": "Wed, 19 Nov 2026 16:00:00 +0000",
            "snippet": "Final reminder to upload your team source code and report to the portal by Sunday.",
            "body": "Dear students, please ensure your GitHub repository is updated and your project presentation slides are uploaded before Sunday 11:59 PM.",
            "status": "INBOX",
        },
        {
            "message_id": "demo_msg_009",
            "subject": "Make $5,000 daily with automated Bitcoin trading robot",
            "sender": "crypto-wealth@bitcoin-doubler-passive.io",
            "date_received": "Wed, 19 Nov 2026 12:30:00 +0000",
            "snippet": "Guaranteed passive crypto income. Join thousands of investors making daily profits.",
            "body": "Start trading cryptocurrency with zero risk! Our AI trading bot guarantees 300% monthly return. Deposit $250 today to start making profits.",
            "status": "INBOX",
        },
        {
            "message_id": "demo_msg_010",
            "subject": "Google Cloud Monthly Billing Statement",
            "sender": "cloud-billing@google.com",
            "date_received": "Wed, 19 Nov 2026 09:15:00 +0000",
            "snippet": "Your invoice for billing account 'CSE Cloud Lab' is now available for review.",
            "body": "Your monthly invoice for Google Cloud services is available. Total charges for this billing cycle were $12.45. View invoice in Cloud Console.",
            "status": "INBOX",
        },
    ]
    return sample_pool[:count]
