import os
import sys
import pytest
import sqlite3

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import (
    init_db, get_db_connection, insert_incident, get_incident_by_token,
    get_all_incidents, update_triage_incident
)
from app.dedup import mask_pii, auto_classify_taxonomy, IncidentDeDuplicator
from app.main import app
from experiments.verify_table_a2 import verify_table_a2

# =====================================================================
# 1. UNIT TESTS
# =====================================================================

class TestUnitIRS:
    def test_pii_masking_email(self):
        text = "Nhân viên phát hiện sự cố: admin.sec@company.com và sec-ops@corp.vn cần kiểm tra."
        sanitized, count = mask_pii(text)
        assert count == 2
        assert "admin.sec@company.com" not in sanitized
        assert "sec-ops@corp.vn" not in sanitized
        assert "[REDACTED_EMAIL]" in sanitized

    def test_pii_masking_ip(self):
        text = "Lưu lượng tấn công xuất phát từ IP trạm 192.168.1.150 và gateway 10.0.0.1."
        sanitized, count = mask_pii(text)
        assert count == 2
        assert "192.168.1.150" not in sanitized
        assert "10.0.0.1" not in sanitized
        assert "[REDACTED_IP]" in sanitized

    def test_pii_masking_phone(self):
        text = "Vui lòng gọi điện thoại nội bộ: 0912345678 hoặc +84987654321 khi có biến."
        sanitized, count = mask_pii(text)
        assert count >= 1
        assert "0912345678" not in sanitized
        assert "[REDACTED_PHONE]" in sanitized

    def test_dedup_similarity_calculation(self):
        dedup = IncidentDeDuplicator(similarity_threshold=0.68)
        text_a = "Phát hiện kho lưu trữ AWS S3 bucket corp-data bị cấu hình công khai trên Internet."
        text_b = "Báo cáo: Bucket S3 corp-data trên AWS mở truy cập công khai do lỗi cấu hình bảo mật."
        text_diff = "Mã độc tống tiền Ransomware mã hóa dữ liệu máy chủ kế toán."

        sim_high = dedup.calculate_similarity(text_a, text_b)
        sim_low = dedup.calculate_similarity(text_a, text_diff)

        assert sim_high > 0.65, f"Expected high similarity for near duplicates, got {sim_high}"
        assert sim_low < 0.40, f"Expected low similarity for distinct topics (well below threshold 0.60), got {sim_low}"

    def test_taxonomy_auto_classifier(self):
        # Critical test
        res_crit = auto_classify_taxonomy("Ransomware đang mã hóa dữ liệu máy tính phòng kế toán và đòi tiền chuộc.")
        assert res_crit["event_type"] == "critical_incident"
        assert res_crit["triage_priority"] == "HIGH"
        assert res_crit["threat_source"] == "malware"

        # Near miss test
        res_near = auto_classify_taxonomy("AWS S3 bucket để public nhưng may mắn chưa ai truy cập, đã đóng lại.")
        assert res_near["event_type"] == "near_miss"
        assert res_near["triage_priority"] == "HIGH"

        # Marginal test
        res_marg = auto_classify_taxonomy("Email phishing mạo danh nhân sự nhưng đã bị bộ lọc spam chặn lại.")
        assert res_marg["event_type"] == "marginal_incident"

    def test_reproducibility_review_table_a2(self):
        # Must verify 100% match with Table A2 of paper tyaf019
        assert verify_table_a2("docs/reproducibility_review.csv") is True


# =====================================================================
# 2. INTEGRATION TESTS (FLASK + SQLITE + FEEDBACK LOOP)
# =====================================================================

class TestIntegrationIRS:
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_full_submission_and_feedback_flow(self, client):
        # 1. Submit a new near miss incident
        payload = {
            "submission_mode": "variant_short",
            "narrative": "Kỹ sư phát hiện AWS S3 bucket backup-financial bị mở public. Liên hệ: engineer@company.com, IP: 10.1.2.3.",
            "quick_severity": "near_miss",
            "is_anonymous": "1"
        }
        res = client.post("/submit", data=payload, follow_redirects=False)
        assert res.status_code == 302
        assert "/receipt/" in res.headers["Location"]

        token = res.headers["Location"].split("/receipt/")[1]
        assert token.startswith("IRS-")

        # 2. Reporter views receipt
        receipt_res = client.get(f"/receipt/{token}")
        assert receipt_res.status_code == 200
        assert token.encode() in receipt_res.data
        # Verify PII was redacted
        assert b"engineer@company.com" not in receipt_res.data
        assert b"[REDACTED_EMAIL]" in receipt_res.data

        # 3. Reporter queries feedback anonymously
        feedback_res = client.get(f"/feedback?token={token}")
        assert feedback_res.status_code == 200
        assert b"PENDING" in feedback_res.data or b"TRIAGED" in feedback_res.data

    def test_deduplication_integration(self, client):
        # Submit master incident
        unique_marker = "secret-vault-12345"
        text1 = f"Hệ thống kho dữ liệu đám mây {unique_marker} bị mở quyền đọc tự do trên mạng Internet."
        res1 = client.post("/submit", data={"submission_mode": "variant_short", "narrative": text1, "is_anonymous": "1"}, follow_redirects=True)
        assert res1.status_code == 200

        # Submit duplicate report of the same incident
        text2 = f"Cảnh báo: Kho lưu trữ {unique_marker} đang ở chế độ công khai trên Internet không cần mật khẩu."
        res2 = client.post("/submit", data={"submission_mode": "variant_short", "narrative": text2, "is_anonymous": "1"}, follow_redirects=True)
        assert res2.status_code == 200
        
        # Verify in database that it was marked duplicate
        incidents = get_all_incidents()
        latest = incidents[0]
        assert latest["is_duplicate"] == 1
        assert latest["master_incident_id"] is not None

    def test_soc_triage_update(self, client):
        incidents = get_all_incidents()
        assert len(incidents) > 0
        target = incidents[0]

        update_payload = {
            "status": "RESOLVED",
            "priority": "HIGH",
            "triage_notes": "Đã thu hồi quyền public, rà soát lại toàn bộ IAM chính sách.",
            "case_learning_summary": "Bài học an toàn: Cần bắt buộc chạy linter bảo mật Terraform trước khi merge code vào production."
        }
        update_res = client.post(f"/triage/update/{target['id']}", data=update_payload, follow_redirects=True)
        assert update_res.status_code == 200

        # Check that feedback endpoint now displays the updated SOC notes and Case-based learning
        fb_res = client.get(f"/feedback?token={target['tracking_token']}")
        assert fb_res.status_code == 200
        assert "RESOLVED".encode() in fb_res.data
        assert "Terraform".encode() in fb_res.data


# =====================================================================
# 3. NEGATIVE & SECURITY TESTS (RESILIENCE & DEFENSE)
# =====================================================================

class TestNegativeAndSecurityIRS:
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_empty_payload_rejection(self, client):
        res = client.post("/submit", data={"narrative": "   ", "submission_mode": "variant_short"}, follow_redirects=True)
        assert res.status_code == 200
        assert "không được để trống".encode('utf-8') in res.data

    def test_sql_injection_defense(self, client):
        # Classic SQL Injection attack attempt
        sqli_payload = "Normal report'; DROP TABLE incidents; SELECT * FROM users WHERE '1'='1"
        res = client.post("/submit", data={"submission_mode": "variant_short", "narrative": sqli_payload, "is_anonymous": "1"}, follow_redirects=True)
        assert res.status_code == 200

        # Verify table still exists and data is intact
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM incidents")
        count = cursor.fetchone()[0]
        conn.close()
        assert count > 0, "SQL Injection compromised the incidents table!"

    def test_xss_protection(self, client):
        # Cross-Site Scripting attempt
        xss_payload = "<script>alert('XSS_ATTACK');</script><b>Injected Bold</b>"
        res = client.post("/submit", data={"submission_mode": "variant_short", "narrative": xss_payload, "is_anonymous": "1"}, follow_redirects=True)
        assert res.status_code == 200
        
        # HTML template auto-escaping must prevent raw unescaped script execution
        assert b"<script>alert('XSS_ATTACK');</script>" not in res.data or b"&lt;script&gt;" in res.data

    def test_invalid_tracking_token(self, client):
        res = client.get("/feedback?token=INVALID-NONEXISTENT-TOKEN-999")
        assert res.status_code == 200
        assert "Không tìm thấy sự cố nào tương ứng".encode('utf-8') in res.data

    def test_oversized_payload_handling(self, client):
        # 25,000 characters payload
        large_narrative = "Phát hiện sự cố bất thường: " + ("lỗi hệ thống liên tục lặp lại. " * 800)
        res = client.post("/submit", data={"submission_mode": "variant_short", "narrative": large_narrative, "is_anonymous": "1"}, follow_redirects=True)
        assert res.status_code == 200
