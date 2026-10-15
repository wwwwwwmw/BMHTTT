import sqlite3
import os
import uuid
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "irs_database.sqlite")

def get_db_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DEFAULT_DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_code TEXT UNIQUE NOT NULL,
        tracking_token TEXT UNIQUE NOT NULL,
        submission_mode TEXT NOT NULL,          -- 'baseline_long' or 'variant_short'
        event_type TEXT NOT NULL,               -- 'marginal_incident', 'near_miss', 'critical_incident'
        threat_actor TEXT NOT NULL,             -- 'external_attacker', 'accidental_insider', 'malicious_insider', 'unknown'
        threat_source TEXT NOT NULL,            -- 'phishing', 'credential_stuffing', 'misconfiguration', 'malware', etc.
        latent_factor TEXT NOT NULL,            -- 'vulnerability', 'predisposing_condition'
        predisposing_condition TEXT,
        adverse_impact TEXT NOT NULL,           -- 'none', 'minor', 'moderate', 'critical'
        reporter_role TEXT NOT NULL,            -- 'Internal', 'External'
        is_anonymous INTEGER NOT NULL DEFAULT 1,
        raw_narrative TEXT NOT NULL,
        sanitized_narrative TEXT NOT NULL,
        pii_masked_count INTEGER NOT NULL DEFAULT 0,
        is_duplicate INTEGER NOT NULL DEFAULT 0,
        master_incident_id INTEGER,
        similarity_score REAL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'PENDING',  -- 'PENDING', 'TRIAGED', 'INVESTIGATING', 'RESOLVED'
        triage_priority TEXT NOT NULL DEFAULT 'MEDIUM', -- 'HIGH', 'MEDIUM', 'LOW'
        triage_notes TEXT,
        case_learning_summary TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (master_incident_id) REFERENCES incidents (id)
    );
    """)
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_tracking_token ON incidents(tracking_token);
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_status ON incidents(status);
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_event_type ON incidents(event_type);
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_is_duplicate ON incidents(is_duplicate);
    """)
    
    conn.commit()
    conn.close()

def generate_tracking_token():
    return f"IRS-{uuid.uuid4().hex[:12].upper()}"

def insert_incident(incident_data, db_path=DEFAULT_DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    token = incident_data.get('tracking_token') or generate_tracking_token()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    # Generate sequential incident_code
    cursor.execute("SELECT COUNT(*) FROM incidents")
    count = cursor.fetchone()[0] + 1
    code = incident_data.get('incident_code') or f"INC-{now_str[:4]}-{count:04d}"
    
    cursor.execute("""
    INSERT INTO incidents (
        incident_code, tracking_token, submission_mode, event_type,
        threat_actor, threat_source, latent_factor, predisposing_condition,
        adverse_impact, reporter_role, is_anonymous, raw_narrative,
        sanitized_narrative, pii_masked_count, is_duplicate,
        master_incident_id, similarity_score, status, triage_priority,
        triage_notes, case_learning_summary, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code,
        token,
        incident_data.get('submission_mode', 'variant_short'),
        incident_data.get('event_type', 'marginal_incident'),
        incident_data.get('threat_actor', 'unknown'),
        incident_data.get('threat_source', 'misconfiguration'),
        incident_data.get('latent_factor', 'vulnerability'),
        incident_data.get('predisposing_condition', ''),
        incident_data.get('adverse_impact', 'none'),
        incident_data.get('reporter_role', 'Internal'),
        1 if incident_data.get('is_anonymous', True) else 0,
        incident_data.get('raw_narrative', ''),
        incident_data.get('sanitized_narrative', incident_data.get('raw_narrative', '')),
        incident_data.get('pii_masked_count', 0),
        1 if incident_data.get('is_duplicate', False) else 0,
        incident_data.get('master_incident_id'),
        incident_data.get('similarity_score', 0.0),
        incident_data.get('status', 'PENDING'),
        incident_data.get('triage_priority', 'MEDIUM'),
        incident_data.get('triage_notes', ''),
        incident_data.get('case_learning_summary', ''),
        incident_data.get('created_at', now_str)
    ))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id, code, token

def get_incident_by_token(token, db_path=DEFAULT_DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE tracking_token = ?", (token.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_incidents(db_path=DEFAULT_DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_triage_incident(incident_id, status, priority, triage_notes, case_learning, db_path=DEFAULT_DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE incidents
    SET status = ?, triage_priority = ?, triage_notes = ?, case_learning_summary = ?
    WHERE id = ?
    """, (status, priority, triage_notes, case_learning, incident_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DEFAULT_DB_PATH)
