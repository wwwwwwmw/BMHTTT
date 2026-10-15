import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz

# =====================================================================
# 1. DATA MINIMIZATION & PII MASKING (CONFIDENTIALITY THEME)
# =====================================================================

EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
IPV4_REGEX = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
PHONE_REGEX = re.compile(r'(?:\+?84|0)(?:3[2-9]|5[6|8|9]|7[0|6-9]|8[1-5]|9[0-9])[0-9]{7}\b|\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b|\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')

def mask_pii(text: str):
    """
    Sanitize narrative text by masking sensitive Personal Identifiable Information (PII)
    such as emails, IP addresses, and phone numbers.
    """
    if not text:
        return text, 0
    
    redaction_count = 0
    
    def repl_email(match):
        nonlocal redaction_count
        redaction_count += 1
        return "[REDACTED_EMAIL]"

    def repl_ip(match):
        nonlocal redaction_count
        redaction_count += 1
        return "[REDACTED_IP]"

    def repl_phone(match):
        nonlocal redaction_count
        redaction_count += 1
        return "[REDACTED_PHONE]"

    sanitized = EMAIL_REGEX.sub(repl_email, text)
    sanitized = IPV4_REGEX.sub(repl_ip, sanitized)
    sanitized = PHONE_REGEX.sub(repl_phone, sanitized)

    return sanitized, redaction_count


# =====================================================================
# 2. TAXONOMY AUTO-CLASSIFIER (FOR VARIANT SHORT FORM)
# =====================================================================

def auto_classify_taxonomy(narrative: str, quick_severity: str = "normal"):
    """
    Automatically suggest Table 1 Taxonomy labels from free-form narrative
    to relieve the reporter from cognitive load while maintaining standardization for SOC.
    """
    text_lower = narrative.lower()

    event_type = "marginal_incident"
    threat_actor = "unknown"
    threat_source = "misconfiguration"
    latent_factor = "vulnerability"
    predisposing_condition = "Thiếu quy trình kiểm soát cấu hình tự động"
    adverse_impact = "none"
    priority = "MEDIUM"

    # 1. Critical Incident Detection
    if any(k in text_lower for k in ["ransomware", "mã hóa", "tống tiền", "trích xuất", "50gb", "tê liệt", "ngưng trệ", "exfiltration", "bị tải xuống"]):
        event_type = "critical_incident"
        threat_actor = "external_attacker"
        threat_source = "malware" if ("ransomware" in text_lower or "mã hóa" in text_lower) else "credential_stuffing"
        latent_factor = "vulnerability"
        adverse_impact = "critical"
        priority = "HIGH"

    # 2. Near Miss Detection
    elif any(k in text_lower for k in ["s3 bucket", "suýt", "may mắn", "chưa ai truy cập", "đã xóa ngay", "cô lập", "ngắt kết nối", "chặn thực thi", "cách ly"]):
        event_type = "near_miss"
        if "s3" in text_lower or "bucket" in text_lower:
            threat_actor = "accidental_insider"
            threat_source = "misconfiguration"
            latent_factor = "vulnerability"
            predisposing_condition = "Thiếu công cụ quét tuân thủ chính sách đám mây tự động"
        elif "email cá nhân" in text_lower or "lỡ gửi" in text_lower or "riêng" in text_lower:
            threat_actor = "accidental_insider"
            threat_source = "social_engineering"
            latent_factor = "predisposing_condition"
            predisposing_condition = "Chưa trang bị giải pháp chống thất thoát dữ liệu DLP"
        elif "edr" in text_lower or "trojan" in text_lower or "powershell" in text_lower:
            threat_actor = "external_attacker"
            threat_source = "malware"
            latent_factor = "vulnerability"
            predisposing_condition = "Người dùng click tệp đính kèm lạ"
        elif "mri" in text_lower or "y tế" in text_lower or "scada" in text_lower:
            threat_actor = "accidental_insider"
            threat_source = "misconfiguration"
            latent_factor = "predisposing_condition"
            predisposing_condition = "Thiết bị OT/y tế kết nối mạng ngoài trái quy định"
        adverse_impact = "none"
        priority = "HIGH"

    # 3. Marginal Incident Detection
    else:
        event_type = "marginal_incident"
        if "phishing" in text_lower or "lừa đảo" in text_lower or "mạo danh" in text_lower:
            threat_actor = "external_attacker"
            threat_source = "phishing"
            latent_factor = "predisposing_condition"
            predisposing_condition = "Quy tắc lọc thư rác gateway chưa cập nhật tên miền mới"
            adverse_impact = "minor"
            priority = "LOW"
        elif "brute" in text_lower or "dò mật khẩu" in text_lower or "mfa" in text_lower:
            threat_actor = "external_attacker"
            threat_source = "credential_stuffing"
            latent_factor = "predisposing_condition"
            predisposing_condition = "Chưa cấu hình giới hạn tần suất đăng nhập (Rate limiting)"
            adverse_impact = "minor"
            priority = "MEDIUM"
        elif "vpn" in text_lower or "cve" in text_lower or "lỗ hổng" in text_lower:
            threat_actor = "unknown"
            threat_source = "misconfiguration"
            latent_factor = "vulnerability"
            predisposing_condition = "Quy trình cập nhật bản vá định kỳ bị trễ"
            adverse_impact = "minor"
            priority = "MEDIUM"
        elif "quẹt thẻ" in text_lower or "tailgating" in text_lower or "người lạ" in text_lower:
            threat_actor = "accidental_insider"
            threat_source = "social_engineering"
            latent_factor = "predisposing_condition"
            predisposing_condition = "Văn hóa an ninh vật lý lỏng lẻo"
            adverse_impact = "minor"
            priority = "LOW"

    if quick_severity == "critical" and event_type != "critical_incident":
        priority = "HIGH"

    return {
        "event_type": event_type,
        "threat_actor": threat_actor,
        "threat_source": threat_source,
        "latent_factor": latent_factor,
        "predisposing_condition": predisposing_condition,
        "adverse_impact": adverse_impact,
        "triage_priority": priority
    }


# =====================================================================
# 3. DE-DUPLICATION ENGINE (HIGH-PERFORMANCE BATCH TF-IDF + RAPIDFUZZ)
# =====================================================================

class IncidentDeDuplicator:
    def __init__(self, similarity_threshold: float = 0.60):
        self.threshold = similarity_threshold

    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate hybrid similarity between two narrative texts using TF-IDF and RapidFuzz.
        """
        if not text_a or not text_b:
            return 0.0

        fuzzy_score = fuzz.token_set_ratio(text_a, text_b) / 100.0
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 1), min_df=1)
            tfidf_mat = vectorizer.fit_transform([text_a, text_b])
            cos_sim = float(cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:2])[0][0])
        except Exception:
            cos_sim = 0.0

        return round(max(cos_sim, fuzzy_score), 4)

    def check_duplicate(self, new_narrative: str, existing_incidents: list):
        """
        Check if the new narrative is a duplicate of any existing incidents.
        Returns: (is_duplicate: bool, master_incident_id: int or None, max_score: float)
        """
        if not existing_incidents or not new_narrative:
            return False, None, 0.0

        # Filter out child duplicates to avoid chained duplicate references
        candidates = [inc for inc in existing_incidents if not (inc.get("is_duplicate") and inc.get("master_incident_id"))]
        if not candidates:
            return False, None, 0.0

        candidate_texts = [inc.get("sanitized_narrative") or inc.get("raw_narrative") or "" for inc in candidates]

        best_match_id = None
        max_score = 0.0

        for inc, cand_text in zip(candidates, candidate_texts):
            score = self.calculate_similarity(new_narrative, cand_text)
            if score > max_score:
                max_score = score
                best_match_id = inc.get("id")

        is_dup = (max_score >= self.threshold)
        return is_dup, (best_match_id if is_dup else None), round(float(max_score), 4)

deduplicator = IncidentDeDuplicator(similarity_threshold=0.60)
