import os
import json
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from app.models import (
    init_db, get_db_connection, insert_incident, get_incident_by_token,
    get_all_incidents, update_triage_incident, DEFAULT_DB_PATH
)
from app.dedup import mask_pii, auto_classify_taxonomy, deduplicator

app = Flask(__name__)
app.secret_key = "dt126_cyber_incident_reporting_system_secret_key"

# Ensure database exists
init_db()

def preload_synthetic_data_if_empty():
    """
    If the database is newly initialized, preload a subset of synthetic cases
    from data/train_cases.csv so that instructors can explore the live system immediately.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM incidents")
    count = cursor.fetchone()[0]
    conn.close()

    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "train_cases.csv")
    if count == 0 and os.path.exists(csv_path):
        print("Preloading realistic cases into SQLite from train_cases.csv...")
        df = pd.read_csv(csv_path).head(30) # Preload 30 representative cases
        
        for _, row in df.iterrows():
            sanitized, pii_count = mask_pii(row['narrative_text'])
            
            # Check de-dup with existing
            existing = get_all_incidents()
            is_dup, master_id, sim_score = deduplicator.check_duplicate(sanitized, existing)
            
            incident_data = {
                "incident_code": row['incident_id'],
                "submission_mode": "variant_short" if row.name % 2 == 0 else "baseline_long",
                "event_type": row['event_type'],
                "threat_actor": row['threat_actor'],
                "threat_source": row['threat_source'],
                "latent_factor": row['latent_factor'],
                "predisposing_condition": row.get('predisposing_condition', ''),
                "adverse_impact": row['adverse_impact'],
                "reporter_role": row['reporter_role'],
                "is_anonymous": bool(row['is_anonymous']),
                "raw_narrative": row['narrative_text'],
                "sanitized_narrative": sanitized,
                "pii_masked_count": pii_count,
                "is_duplicate": is_dup,
                "master_incident_id": master_id,
                "similarity_score": sim_score,
                "status": "TRIAGED" if is_dup else ("INVESTIGATING" if row['event_type'] == 'critical_incident' else "PENDING"),
                "triage_priority": "HIGH" if row['event_type'] in ['critical_incident', 'near_miss'] else "LOW",
                "triage_notes": "Đã ghi nhận và xử lý sơ bộ theo quy trình ứng cứu." if is_dup else "",
                "case_learning_summary": "Tăng cường giám sát và rà soát cấu hình liên quan." if is_dup else ""
            }
            insert_incident(incident_data)
        print("Preloading completed successfully!")

preload_synthetic_data_if_empty()

@app.route("/")
def index():
    incidents = get_all_incidents()
    total_count = len(incidents)
    critical_count = sum(1 for i in incidents if i['event_type'] == 'critical_incident')
    near_miss_count = sum(1 for i in incidents if i['event_type'] == 'near_miss')
    duplicate_count = sum(1 for i in incidents if i['is_duplicate'] == 1)
    masked_pii_count = sum(i['pii_masked_count'] for i in incidents)

    return render_template(
        "index.html",
        total_count=total_count,
        critical_count=critical_count,
        near_miss_count=near_miss_count,
        duplicate_count=duplicate_count,
        masked_pii_count=masked_pii_count
    )

@app.route("/report/variant")
def report_variant():
    return render_template("report_variant.html")

@app.route("/report/baseline")
def report_baseline():
    return render_template("report_baseline.html")

@app.route("/submit", methods=["POST"])
def submit_incident():
    mode = request.form.get("submission_mode", "variant_short")
    raw_narrative = request.form.get("narrative", "").strip()
    is_anonymous = bool(request.form.get("is_anonymous"))

    if not raw_narrative:
        flash("Nội dung mô tả sự cố không được để trống!", "danger")
        return redirect(url_for("report_variant" if mode == "variant_short" else "report_baseline"))

    # 1. Confidentiality / Data Minimization: Mask PII if anonymous or requested
    sanitized_narrative, pii_count = mask_pii(raw_narrative) if is_anonymous else (raw_narrative, 0)

    # 2. De-duplication check against existing incidents in database
    existing_incidents = get_all_incidents()
    is_dup, master_id, sim_score = deduplicator.check_duplicate(sanitized_narrative, existing_incidents)

    # 3. Taxonomy Extraction: Auto-classify if Variant Form, or use manual values if Baseline
    if mode == "variant_short":
        quick_sev = request.form.get("quick_severity", "normal")
        predicted = auto_classify_taxonomy(raw_narrative, quick_severity=quick_sev)
        event_type = predicted["event_type"]
        threat_actor = predicted["threat_actor"]
        threat_source = predicted["threat_source"]
        latent_factor = predicted["latent_factor"]
        predisposing_condition = predicted["predisposing_condition"]
        adverse_impact = predicted["adverse_impact"]
        priority = predicted["triage_priority"]
        reporter_role = "Internal"
    else:
        event_type = request.form.get("event_type", "marginal_incident")
        threat_actor = request.form.get("threat_actor", "unknown")
        threat_source = request.form.get("threat_source", "misconfiguration")
        latent_factor = request.form.get("latent_factor", "vulnerability")
        predisposing_condition = request.form.get("predisposing_condition", "")
        adverse_impact = request.form.get("adverse_impact", "none")
        reporter_role = request.form.get("reporter_role", "Internal")
        priority = "HIGH" if event_type in ["critical_incident", "near_miss"] else "MEDIUM"

    # Save to SQLite database
    incident_data = {
        "submission_mode": mode,
        "event_type": event_type,
        "threat_actor": threat_actor,
        "threat_source": threat_source,
        "latent_factor": latent_factor,
        "predisposing_condition": predisposing_condition,
        "adverse_impact": adverse_impact,
        "reporter_role": reporter_role,
        "is_anonymous": is_anonymous,
        "raw_narrative": raw_narrative,
        "sanitized_narrative": sanitized_narrative,
        "pii_masked_count": pii_count,
        "is_duplicate": is_dup,
        "master_incident_id": master_id,
        "similarity_score": sim_score,
        "status": "TRIAGED" if is_dup else "PENDING",
        "triage_priority": priority,
        "triage_notes": f"Tự động gom nhóm trùng với Master Incident #{master_id} (Độ tương đồng: {sim_score*100:.1f}%)." if is_dup else "",
        "case_learning_summary": ""
    }

    new_id, code, token = insert_incident(incident_data)
    return redirect(url_for("receipt", token=token))

@app.route("/receipt/<token>")
def receipt(token):
    incident = get_incident_by_token(token)
    if not incident:
        return "Không tìm thấy báo cáo sự cố!", 404
    return render_template("receipt.html", incident=incident)

@app.route("/feedback", methods=["GET"])
def feedback():
    token = request.args.get("token", "").strip()
    incident = None
    error = None

    if token:
        incident = get_incident_by_token(token)
        if not incident:
            error = f"Không tìm thấy sự cố nào tương ứng với mã Tracking Token: '{token}'. Vui lòng kiểm tra lại!"

    return render_template("feedback.html", token=token, incident=incident, error=error)

@app.route("/triage")
def triage():
    incidents = get_all_incidents()
    
    # Priority sorting: Critical and Near Miss first, then by priority
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    event_order = {"critical_incident": 0, "near_miss": 1, "marginal_incident": 2}

    incidents_sorted = sorted(
        incidents,
        key=lambda x: (
            event_order.get(x['event_type'], 3),
            priority_order.get(x['triage_priority'], 2),
            -x['id']
        )
    )

    critical_count = sum(1 for i in incidents if i['event_type'] == 'critical_incident')
    near_miss_count = sum(1 for i in incidents if i['event_type'] == 'near_miss')
    duplicate_count = sum(1 for i in incidents if i['is_duplicate'] == 1)

    return render_template(
        "triage.html",
        incidents=incidents_sorted,
        critical_count=critical_count,
        near_miss_count=near_miss_count,
        duplicate_count=duplicate_count
    )

@app.route("/triage/update/<int:incident_id>", methods=["POST"])
def update_triage(incident_id):
    status = request.form.get("status", "PENDING")
    priority = request.form.get("priority", "MEDIUM")
    triage_notes = request.form.get("triage_notes", "")
    case_learning = request.form.get("case_learning_summary", "")

    update_triage_incident(incident_id, status, priority, triage_notes, case_learning)
    return redirect(url_for("triage"))

@app.route("/api/metrics")
def api_metrics():
    incidents = get_all_incidents()
    total = len(incidents)
    duplicates = sum(1 for i in incidents if i['is_duplicate'] == 1)
    
    event_counts = {}
    for i in incidents:
        event_counts[i['event_type']] = event_counts.get(i['event_type'], 0) + 1

    return jsonify({
        "total_reports": total,
        "unique_master_incidents": total - duplicates,
        "duplicate_reports": duplicates,
        "duplicate_rate": round(duplicates / total, 4) if total > 0 else 0.0,
        "event_distribution": event_counts,
        "pii_masked_total": sum(i['pii_masked_count'] for i in incidents)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
