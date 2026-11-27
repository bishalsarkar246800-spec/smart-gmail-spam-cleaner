import sqlite3


def get_database_connection(database_path="emails.db"):
    """
    Establishes a connection to the SQLite database and configures row access by column name.
    Takes the database path string and returns an active sqlite3.Connection object.
    """
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path="emails.db"):
    """
    Creates the scanned_emails table and relevant indexes if they do not already exist.
    Takes the SQLite database file path string and returns None.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS scanned_emails (
        message_id TEXT PRIMARY KEY,
        subject TEXT,
        sender TEXT,
        date_received TEXT,
        snippet TEXT,
        body TEXT,
        spam_probability REAL,
        is_spam INTEGER,
        status TEXT DEFAULT 'INBOX',
        scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    create_index_query = """
    CREATE INDEX IF NOT EXISTS idx_scanned_at ON scanned_emails(scanned_at DESC);
    """
    with get_database_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(create_table_query)
        cursor.execute(create_index_query)
        connection.commit()


def insert_scanned_emails_batch(email_records, database_path="emails.db"):
    """
    Inserts a collection of scanned email records while updating metrics on message ID conflict.
    Takes a list of email dictionaries and database path, returning the count of inserted records.
    """
    upsert_query = """
    INSERT INTO scanned_emails (
        message_id,
        subject,
        sender,
        date_received,
        snippet,
        body,
        spam_probability,
        is_spam,
        status
    ) VALUES (
        :message_id,
        :subject,
        :sender,
        :date_received,
        :snippet,
        :body,
        :spam_probability,
        :is_spam,
        :status
    )
    ON CONFLICT(message_id) DO UPDATE SET
        spam_probability = excluded.spam_probability,
        is_spam = excluded.is_spam,
        scanned_at = CURRENT_TIMESTAMP;
    """
    with get_database_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.executemany(upsert_query, email_records)
        connection.commit()
        return cursor.rowcount


def fetch_scan_history(limit=100, database_path="emails.db"):
    """
    Retrieves logged email scan history from the database ordered chronologically descending.
    Takes the integer fetch limit and database path string, returning a list of email dictionaries.
    """
    safe_limit = max(1, min(int(limit), 1000))
    fetch_query = """
    SELECT
        message_id,
        subject,
        sender,
        date_received,
        snippet,
        body,
        spam_probability,
        is_spam,
        status,
        scanned_at
    FROM scanned_emails
    ORDER BY scanned_at DESC
    LIMIT ?;
    """
    with get_database_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(fetch_query, (safe_limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_emails_status_batch(message_ids, new_status="TRASHED", database_path="emails.db"):
    """
    Updates the status attribute for a list of message IDs, such as marking moved emails as TRASHED.
    Takes a list of message ID strings, status string, and database path, returning modified rows count.
    """
    allowed_statuses = {"INBOX", "TRASHED", "ARCHIVED", "SCANNED"}
    sanitized_status = str(new_status).upper().strip()
    if sanitized_status not in allowed_statuses:
        sanitized_status = "TRASHED"

    clean_message_ids = [str(mid).strip() for mid in message_ids if str(mid).strip()]
    if not clean_message_ids:
        return 0

    total_updated = 0
    batch_size = 100
    with get_database_connection(database_path) as connection:
        cursor = connection.cursor()
        for index in range(0, len(clean_message_ids), batch_size):
            chunk = clean_message_ids[index : index + batch_size]
            placeholders = ",".join(["?"] * len(chunk))
            update_query = f"""
            UPDATE scanned_emails
            SET status = ?
            WHERE message_id IN ({placeholders});
            """
            cursor.execute(update_query, [sanitized_status] + chunk)
            total_updated += cursor.rowcount
        connection.commit()
        return total_updated


def fetch_email_statistics(database_path="emails.db"):
    """
    Computes aggregate metrics including total scanned, spam count, ham count, and trashed count.
    Takes the database path string and returns a dictionary containing computed summary totals.
    """
    stats_query = """
    SELECT
        COUNT(*) AS total_scanned,
        SUM(CASE WHEN is_spam = 1 THEN 1 ELSE 0 END) AS total_spam,
        SUM(CASE WHEN is_spam = 0 THEN 1 ELSE 0 END) AS total_ham,
        SUM(CASE WHEN status = 'TRASHED' THEN 1 ELSE 0 END) AS total_trashed
    FROM scanned_emails;
    """
    with get_database_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(stats_query)
        result = cursor.fetchone()
        return {
            "total_scanned": result["total_scanned"] or 0,
            "total_spam": result["total_spam"] or 0,
            "total_ham": result["total_ham"] or 0,
            "total_trashed": result["total_trashed"] or 0,
        }
