import os
import json
import random
import hashlib
import numpy as np
import pandas as pd
from faker import Faker

def generate_synthetic_incidents(seed=42, total_target=400, train_ratio=0.7):
    # Set seeds for complete reproducibility
    random.seed(seed)
    np.random.seed(seed)
    fake = Faker()
    Faker.seed(seed)

    # Scenarios grounded in Table 1 of paper tyaf019
    cluster_templates = [
        # 1. AWS S3 bucket public
        {
            "topic": "AWS S3 Bucket Public Misconfiguration",
            "event_type": "near_miss",
            "threat_actor": "accidental_insider",
            "threat_source": "misconfiguration",
            "latent_factor": "vulnerability",
            "predisposing_condition": "DevOps lack of automated cloud compliance scanning",
            "adverse_impact": "none",
            "narratives": [
                "Phát hiện S3 bucket '{bucket}' chứa dữ liệu hồ sơ khách hàng đang ở chế độ public read do nhân viên DevOps cấu hình sai chính sách IAM. Kiểm tra CloudTrail chưa thấy truy cập bất thường.",
                "Cảnh báo: Bucket AWS S3 tên '{bucket}' để mở truy cập công khai không cần xác thực. Đã phát hiện và sửa quyền lại thành private ngay lập tức, chưa có dấu hiệu rò rỉ ra ngoài.",
                "Tôi thấy bucket '{bucket}' lưu thông tin khách hàng bị công khai trên Internet do nhầm lẫn quyền IAM lúc deploy bản cập nhật sáng nay. May mắn là chưa ai tải xuống.",
                "Báo cáo sự cố suýt xảy ra: Kho lưu trữ đám mây '{bucket}' trên AWS có thể bị người ngoài xem tự do do lỗi cấu hình bảo mật. Đã đóng quyền công khai sau 15 phút."
            ]
        },
        # 2. Ransomware outbreak
        {
            "topic": "Ransomware Encryption Incident",
            "event_type": "critical_incident",
            "threat_actor": "external_attacker",
            "threat_source": "malware",
            "latent_factor": "vulnerability",
            "predisposing_condition": "Hệ thống legacy chưa vá lỗ hổng SMBv1 và phân quyền mạng chưa cô lập",
            "adverse_impact": "critical",
            "narratives": [
                "Hệ thống máy chủ chia sẻ tệp tin tại văn phòng chi nhánh bị mã độc tống tiền Ransomware khóa toàn bộ dữ liệu. Xuất hiện tệp README_DECRYPT.txt đòi tiền chuộc 2 BTC.",
                "Nhiều máy tính trong mạng nội bộ bị mã hóa đuôi .locked, màn hình hiện thông báo đòi tiền chuộc. Dịch vụ lưu trữ dữ liệu chung đang bị tê liệt hoàn toàn.",
                "Khẩn cấp: Tấn công Ransomware đang lây lan trên các máy chủ dữ liệu phòng Kế toán. Các file chia sẻ đã bị mã hóa, nhân viên không thể truy cập tài liệu nghiệp vụ.",
                "Báo cáo sự cố nghiêm trọng: Mã độc tống tiền lây lan qua máy chủ file server lúc rạng sáng, làm gián đoạn toàn bộ hoạt động kinh doanh và sao lưu dữ liệu."
            ]
        },
        # 3. Phishing blocked by filter / user report
        {
            "topic": "Phishing Email Campaign",
            "event_type": "marginal_incident",
            "threat_actor": "external_attacker",
            "threat_source": "phishing",
            "latent_factor": "predisposing_condition",
            "predisposing_condition": "Bộ lọc thư rác gateway chưa cập nhật rule nhận diện tên miền giả mạo mới",
            "adverse_impact": "minor",
            "narratives": [
                "Nhận được email giả mạo thông báo cập nhật lương từ phòng Nhân sự với liên kết lạ 'http://{domain}/login'. Chưa có ai bấm vào liên kết, đã chuyển tiếp cho SOC kiểm tra.",
                "Email lừa đảo mạo danh ngân hàng gửi đến hộp thư nội bộ yêu cầu xác nhận tài khoản tại '{domain}'. Người dùng phát hiện sớm và thông báo tới quản trị mạng.",
                "Phát hiện chiến dịch phishing mạo danh Office 365 gửi tới nhân viên phòng Marketing qua domain '{domain}'. Hệ thống lọc thư đã chặn một phần.",
                "Tôi nhận được thư đòi đổi mật khẩu tài khoản công ty gửi từ địa chỉ giả mạo. Đường link dẫn tới trang web giả lập giao diện Microsoft '{domain}'."
            ]
        },
        # 4. Brute force on MFA portal
        {
            "topic": "Brute Force on MFA Portal",
            "event_type": "marginal_incident",
            "threat_actor": "external_attacker",
            "threat_source": "credential_stuffing",
            "latent_factor": "predisposing_condition",
            "predisposing_condition": "Chưa bật giới hạn tốc độ truy cập (Rate limiting) tại reverse proxy",
            "adverse_impact": "minor",
            "narratives": [
                "Hệ thống phát hiện hơn 2,000 lượt thử mật khẩu liên tục vào cổng đăng nhập VPN từ dải IP nước ngoài. Tất cả đều bị chặn do yêu cầu xác thực 2 bước (MFA).",
                "Ghi nhận đợt tấn công brute-force vào cổng SSO nội bộ. Kẻ tấn công thử mật khẩu nhiều tài khoản nhưng không thành công vì hệ thống yêu cầu mã OTP qua điện thoại.",
                "Cảnh báo tự động từ WAF: Phát hiện hành vi dò mật khẩu tài khoản người dùng tại trang login. Chưa tài khoản nào bị chiếm quyền nhờ lớp bảo vệ đa yếu tố MFA."
            ]
        },
        # 5. Client data sent to private email by mistake
        {
            "topic": "Accidental PII Email Forward",
            "event_type": "near_miss",
            "threat_actor": "accidental_insider",
            "threat_source": "social_engineering",
            "latent_factor": "predisposing_condition",
            "predisposing_condition": "Thiếu giải pháp phòng chống thất thoát dữ liệu (DLP) tại máy trạm",
            "adverse_impact": "none",
            "narratives": [
                "Nhân viên quản lý khách hàng do sơ suất đã gửi danh sách khách hàng gồm họ tên và số điện thoại về email cá nhân để làm việc tại nhà, nhưng đã tự giác xóa ngay và báo cáo.",
                "Tôi lỡ gửi nhầm bảng thống kê thông tin đối tác vào địa chỉ email cá nhân thay vì email công vụ. Tôi đã xóa vĩnh viễn trong thùng rác và cam kết không lưu bản sao.",
                "Báo cáo sự cố suýt rò rỉ: Nhân viên vô tình đính kèm tệp thông tin giao dịch vào email riêng. Đã thực hiện thu hồi thư và tự nguyện khai báo với bộ phận bảo mật."
            ]
        },
        # 6. EDR halted malware execution
        {
            "topic": "Endpoint Malware Quarantined",
            "event_type": "near_miss",
            "threat_actor": "external_attacker",
            "threat_source": "malware",
            "latent_factor": "vulnerability",
            "predisposing_condition": "Nhân viên vô tình tải file đính kèm độc hại từ email quảng cáo",
            "adverse_impact": "none",
            "narratives": [
                "Nhân viên tải xuống tệp tin nén chứa mã độc Trojan từ Internet. Phần mềm bảo vệ điểm cuối (EDR) đã chặn thực thi và cô lập tệp kịp thời.",
                "Cảnh báo EDR: Phát hiện hành vi thực thi script độc hại PowerShell trên máy trạm của nhân viên thiết kế. EDR đã tiêu diệt tiến trình trước khi tạo persistence.",
                "Phát hiện mã độc trojan ẩn trong file hợp đồng PDF tải về máy cá nhân. Chương trình diệt virus tự động cách ly tập tin, không có dữ liệu nào bị tổn hại."
            ]
        },
        # 7. Unpatched VPN Client Vulnerability
        {
            "topic": "Zero-day/N-day VPN Client Vulnerability",
            "event_type": "marginal_incident",
            "threat_actor": "unknown",
            "threat_source": "misconfiguration",
            "latent_factor": "vulnerability",
            "predisposing_condition": "Quy trình quản lý bản vá (Patch Management) chậm trễ",
            "adverse_impact": "minor",
            "narratives": [
                "Kỹ sư mạng phát hiện phiên bản phần mềm VPN Gateway đang sử dụng có lỗ hổng CVE nghiêm trọng cho phép vượt qua xác thực. Cần khẩn cấp nâng cấp phiên bản vá lỗi.",
                "Hãng bảo mật vừa công bố lỗ hổng RCE trên thiết bị VPN của công ty chúng ta. Hiện tại chưa phát hiện dấu hiệu khai thác trong log nhưng cần vá ngay lập tức.",
                "Báo cáo lỗ hổng: Cổng kết nối từ xa VPN SSL chưa được áp dụng bản vá bảo mật mới nhất, tiềm ẩn nguy cơ bị chiếm quyền truy cập nếu tin tặc quét cổng."
            ]
        },
        # 8. Unauthorized Physical Badging
        {
            "topic": "Physical Entry Tailgating",
            "event_type": "marginal_incident",
            "threat_actor": "accidental_insider",
            "threat_source": "social_engineering",
            "latent_factor": "predisposing_condition",
            "predisposing_condition": "Văn hóa an ninh vật lý lỏng lẻo, nhân viên ngại từ chối người lạ",
            "adverse_impact": "minor",
            "narratives": [
                "Một nhân viên đã quẹt thẻ cửa và giữ cửa cho một người lạ đi vào khu vực phòng máy chủ mà không xuất trình thẻ khách. Bảo vệ đã chặn lại để kiểm tra thẻ.",
                "Báo cáo vi phạm an ninh vật lý: Khách vãng lai đi theo sau nhân viên vào khu vực làm việc bảo mật (tailgating). Người này sau đó đã được mời ra phòng tiếp tân.",
                "Tôi vô tình mở cửa cho người tự xưng là thợ sửa chữa vào tầng kỹ thuật khi chưa kiểm tra giấy phép công tác. Đã báo ngay cho đội an ninh tòa nhà xử lý."
            ]
        },
        # 9. Legacy Industrial Controller / OT Network
        {
            "topic": "OT Medical/Industrial Device Connected Outside",
            "event_type": "near_miss",
            "threat_actor": "accidental_insider",
            "threat_source": "misconfiguration",
            "latent_factor": "predisposing_condition",
            "predisposing_condition": "Hạ tầng mạng OT y tế/công nghiệp kết nối thẳng ra ngoài Internet",
            "adverse_impact": "none",
            "narratives": [
                "Bác sĩ chuyên khoa báo cáo máy chụp cộng hưởng từ (MRI) chạy hệ điều hành Windows 7 cũ bị nối nhầm vào mạng Wi-Fi công cộng. Đã rút dây mạng cô lập thiết bị.",
                "Thiết bị giám sát y tế trong bệnh viện đang mở cổng điều khiển từ xa Telnet ra ngoài Internet không có mật khẩu. Đã cấu hình lại router để chặn truy cập.",
                "Kỹ sư điều khiển phát hiện hệ thống máy tính công nghiệp SCADA kết nối ra ngoài mà không qua tường lửa riêng biệt. Đã ngắt kết nối mạng ngay lập tức."
            ]
        },
        # 10. Data Extraction Incident (Critical)
        {
            "topic": "Confidential Database Exfiltration",
            "event_type": "critical_incident",
            "threat_actor": "external_attacker",
            "threat_source": "credential_stuffing",
            "latent_factor": "vulnerability",
            "predisposing_condition": "Tài khoản quản trị viên cơ sở dữ liệu không bật xác thực 2 bước",
            "adverse_impact": "critical",
            "narratives": [
                "SOC phát hiện lưu lượng dữ liệu bất thường 50GB được trích xuất từ cơ sở dữ liệu khách hàng chuyển về máy chủ lạ tại Đông Âu thông qua tài khoản DBA bị chiếm đoạt.",
                "Cơ sở dữ liệu thông tin tài chính người dùng bị trích xuất trái phép qua API nội bộ. Kẻ tấn công sử dụng thông tin đăng nhập rò rỉ của nhân viên quản trị.",
                "Sự cố rò rỉ dữ liệu nghiêm trọng: Toàn bộ bảng thông tin thẻ thanh toán và lịch sử giao dịch đã bị tải xuống máy chủ bên ngoài lúc 2 giờ sáng."
            ]
        }
    ]

    records = []
    cluster_id = 1

    # Generate roughly 120 - 150 clusters
    while len(records) < total_target:
        tmpl = random.choice(cluster_templates)
        
        # Decide cluster size (1 = singleton, 2-4 = duplicates / near duplicates)
        # 40% singletons, 60% clusters with 2-4 reports
        cluster_size = 1 if random.random() < 0.35 else random.randint(2, 4)
        
        # Determine cluster-wide dynamic entities
        bucket_name = f"corp-data-{fake.domain_word()}-{random.randint(100, 999)}"
        phish_domain = f"auth-{fake.domain_word()}.{random.choice(['xyz', 'top', 'info', 'live'])}"
        
        for rep_idx in range(cluster_size):
            # Select narrative variant
            base_narrative = random.choice(tmpl["narratives"])
            narrative = base_narrative.format(bucket=bucket_name, domain=phish_domain)
            
            # Add PII to narrative for testing data minimization
            has_pii = random.random() < 0.65
            reporter_email = fake.email()
            reporter_phone = fake.phone_number()
            reporter_ip = fake.ipv4()
            
            if has_pii:
                pii_insertion_type = random.choice(["email", "phone", "ip", "all"])
                if pii_insertion_type == "email":
                    narrative += f" Người phát hiện và liên hệ: {reporter_email}."
                elif pii_insertion_type == "phone":
                    narrative += f" Vui lòng gọi số nội bộ: {reporter_phone} khi cần đối soát."
                elif pii_insertion_type == "ip":
                    narrative += f" Máy trạm gửi báo cáo có IP: {reporter_ip}."
                else:
                    narrative += f" Liên hệ: {reporter_email}, ĐT: {reporter_phone}, IP trạm: {reporter_ip}."

            is_anonymous = random.choice([True, False])
            reporter_role = random.choice(["Internal", "External"])

            record = {
                "incident_id": f"INC-{len(records)+1:04d}",
                "cluster_id": cluster_id,
                "is_duplicate_ground_truth": (rep_idx > 0),
                "topic": tmpl["topic"],
                "event_type": tmpl["event_type"],
                "threat_actor": tmpl["threat_actor"],
                "threat_source": tmpl["threat_source"],
                "latent_factor": tmpl["latent_factor"],
                "predisposing_condition": tmpl["predisposing_condition"],
                "adverse_impact": tmpl["adverse_impact"],
                "is_anonymous": is_anonymous,
                "reporter_role": reporter_role,
                "narrative_text": narrative,
                "has_pii": has_pii,
                "raw_pii_email": reporter_email if has_pii else "",
                "raw_pii_phone": reporter_phone if has_pii else "",
                "raw_pii_ip": reporter_ip if has_pii else ""
            }
            records.append(record)
            if len(records) >= total_target:
                break
        cluster_id += 1

    # Shuffle clusters to prepare train/test split without leakage
    all_clusters = sorted(list(set(r["cluster_id"] for r in records)))
    random.shuffle(all_clusters)
    
    n_train_clusters = int(len(all_clusters) * train_ratio)
    train_cluster_set = set(all_clusters[:n_train_clusters])
    test_cluster_set = set(all_clusters[n_train_clusters:])

    train_records = []
    test_records = []

    for r in records:
        if r["cluster_id"] in train_cluster_set:
            r["split"] = "train"
            train_records.append(r)
        else:
            r["split"] = "test"
            test_records.append(r)

    # Verify no cluster overlap
    overlap = set(r["cluster_id"] for r in train_records).intersection(set(r["cluster_id"] for r in test_records))
    assert len(overlap) == 0, f"DATA LEAKAGE DETECTED! Overlapping clusters: {overlap}"

    # Save raw_synthetic_cases.json
    with open('data/raw_synthetic_cases.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # Save train_cases.csv and test_cases.csv
    df_all = pd.DataFrame(records)
    df_train = pd.DataFrame(train_records)
    df_test = pd.DataFrame(test_records)

    df_train.to_csv('data/train_cases.csv', index=False, encoding='utf-8-sig')
    df_test.to_csv('data/test_cases.csv', index=False, encoding='utf-8-sig')

    # Compute SHA-256 Checksums
    def get_sha256(filepath):
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    raw_hash = get_sha256('data/raw_synthetic_cases.json')
    train_hash = get_sha256('data/train_cases.csv')
    test_hash = get_sha256('data/test_cases.csv')

    # Calculate class distribution statistics
    event_counts = df_all['event_type'].value_counts().to_dict()
    total_recs = len(df_all)
    dup_recs = int(df_all['is_duplicate_ground_truth'].sum())

    manifest_content = f"""# DATASET MANIFEST & INTEGRITY SPECIFICATION
# Project: DT126-IRS-Repro (Incident Reporting System based on Safety Science)
# Reference: DOI 10.1093/cybsec/tyaf019
# Version: 1.0.0
# Generator Seed: {seed}
# Creation Date: 2026-10-15

[SHA256 Checksums]
{raw_hash}  data/raw_synthetic_cases.json
{train_hash}  data/train_cases.csv
{test_hash}  data/test_cases.csv

[Dataset Summary & Statistics]
Total Incident Records: {total_recs}
Total Unique Clusters: {len(all_clusters)}
Duplicate Ground Truth Records: {dup_recs} ({dup_recs/total_recs*100:.2f}%)
Train Records: {len(df_train)} ({len(train_cluster_set)} clusters)
Test Records: {len(df_test)} ({len(test_cluster_set)} clusters)
Cluster Overlap Between Train and Test: 0 (Strict Cluster Split - Zero Data Leakage)

[Class Distribution (Table 1 Taxonomy)]
- Marginal Incident: {event_counts.get('marginal_incident', 0)} ({event_counts.get('marginal_incident', 0)/total_recs*100:.2f}%)
- Near Miss: {event_counts.get('near_miss', 0)} ({event_counts.get('near_miss', 0)/total_recs*100:.2f}%)
- Critical Incident: {event_counts.get('critical_incident', 0)} ({event_counts.get('critical_incident', 0)/total_recs*100:.2f}%)

[Latent Factors Distribution]
- Vulnerability: {int((df_all['latent_factor'] == 'vulnerability').sum())}
- Predisposing Condition: {int((df_all['latent_factor'] == 'predisposing_condition').sum())}

[Threat Actors Distribution]
{json.dumps(df_all['threat_actor'].value_counts().to_dict(), indent=2)}

[Trust Boundary & Data Minimization]
Trust Boundary: Reporter -> Web Form -> PII Masking Filter -> SQLite DB -> SOC Triage Queue.
PII Injected Records: {int(df_all['has_pii'].sum())} records containing raw emails, phone numbers, or IPv4 addresses for privacy leakage testing.
"""

    with open('data/manifest.sha256', 'w', encoding='utf-8') as f:
        f.write(manifest_content)

    print("Synthetic data generation completed successfully!")
    print(f"Generated {total_recs} records across {len(all_clusters)} clusters.")
    print(f"Train set: {len(df_train)} rows | Test set: {len(df_test)} rows.")
    print("Zero train-test leakage verified.")

if __name__ == "__main__":
    generate_synthetic_incidents(seed=42, total_target=400, train_ratio=0.7)
