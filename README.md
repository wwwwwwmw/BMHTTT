# DT126-IRS-Repro: Tái Lập & Thực Nghiệm Hệ Thống Báo Cáo Sự Cố An Ninh Mạng (IRS) Dựa Trên Khoa Học An Toàn (Safety Science)

Dự án tái lập bài báo khoa học:
> **Designing incident reporting systems in cybersecurity**  
> *Tobias A. Schaltegger, Benjamin Ambuehl, Melanie Knieps, Alain Mermoud, David Basin, Vincent Lenders*  
> **Journal of Cybersecurity**, Volume 11, Issue 1, 2025, tyaf019 (Oxford University Press)  
> DOI: [10.1093/cybsec/tyaf019](https://doi.org/10.1093/cybsec/tyaf019)

---

## 1. Cấu Trúc Thư Mục Dự Án

```plaintext
BMHTTT_DT126/
├── docs/
│   ├── phieu_tai_lap_tyaf019.md       # Phiếu tái lập bài báo chi tiết (Mục 1)
│   ├── reproducibility_review.csv     # Bảng đối chiếu 37 bài báo & Table A2
│   ├── figures/                       # Các biểu đồ EDA & Thực nghiệm đã vẽ
│   │   ├── eda_class_and_latent_distribution.png
│   │   ├── eda_cluster_and_actor_distribution.png
│   │   ├── eda_text_length_by_event.png
│   │   └── experiment_comparison.png
├── data/
│   ├── raw_synthetic_cases.json       # Dữ liệu 400 ca sự cố giả lập gốc (Table 1)
│   ├── train_cases.csv                # Tập train phân cụm (tránh data leakage)
│   ├── test_cases.csv                 # Tập test phân cụm
│   └── manifest.sha256                # Checksum SHA-256 + metadata của dataset
├── app/
│   ├── main.py                        # Web server (Flask) & API
│   ├── models.py                      # SQLite Schema & ORM theo Taxonomy Bảng 1
│   ├── dedup.py                       # Khử trùng lặp (TF-IDF + RapidFuzz) & Che PII
│   ├── irs_database.sqlite            # Cơ sở dữ liệu SQLite
│   └── templates/                     # Giao diện Web (Base, Index, Baseline, Variant, Receipt, Feedback, Triage)
├── experiments/
│   ├── generate_data.py               # Script sinh dữ liệu với seed=42 cố định
│   ├── eda_and_plots.py               # Thống kê chất lượng dữ liệu & vẽ biểu đồ EDA
│   ├── run_experiments.py             # Chạy 3 lần thực nghiệm đối chứng, đo metrics
│   ├── verify_table_a2.py             # Script đối chiếu kiểm chứng 100% Bảng A2
│   ├── experiment_results.csv         # Bảng số liệu chi tiết qua 3 runs
│   └── experiment_summary.md          # Báo cáo phân tích thực nghiệm kèm Mean ± Std
├── tests/
│   └── test_irs.py                    # Unit, Integration, Negative & Security tests (pytest)
├── requirements.txt                   # Danh sách thư viện khóa cứng phiên bản
└── tyaf019.pdf                        # File bài báo gốc
```

---

## 2. Hướng Dẫn Cài Đặt & Chạy Hệ Thống

### 2.1. Kích hoạt môi trường ảo Python
```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Hoặc cài đặt dependencies nếu chưa có
pip install -r requirements.txt
```

### 2.2. Kiểm chứng Tái lập Bảng A2 của bài báo gốc
```bash
python experiments/verify_table_a2.py
```
*Kết quả:* Khớp 100% 14 design themes và phân bổ 33 bài y tế + 4 bài hàng không từ Bảng A2 bài báo gốc.

### 2.3. Chạy 3 lần thực nghiệm độc lập (Seeds: 42, 100, 2026)
```bash
python experiments/run_experiments.py
```
*Kết quả:* Xuất bảng kết quả `experiments/experiment_results.csv`, báo cáo `experiments/experiment_summary.md` và biểu đồ đối chứng `docs/figures/experiment_comparison.png`.

### 2.4. Chạy toàn bộ bộ kiểm thử tự động (pytest)
```bash
pytest tests/test_irs.py -v
```
*Kết quả:* Vượt qua 100% (14/14 tests) bao gồm Unit test PII/Dedup, Integration test Web Flow, Negative test (SQL Injection, XSS, Oversized payload).

### 2.5. Khởi chạy Ứng Dụng Web Prototype
```bash
python -m app.main
```
Truy cập trình duyệt tại: `http://127.0.0.1:5000`
- **Giao diện Form Ngắn (Cải tiến):** `http://127.0.0.1:5000/report/variant`
- **Giao diện Form Dài (Baseline):** `http://127.0.0.1:5000/report/baseline`
- **Tra cứu Phản hồi Ẩn danh (Tracking Token):** `http://127.0.0.1:5000/feedback`
- **Hàng đợi Phân loại SOC (Triage Queue):** `http://127.0.0.1:5000/triage`
- **API Thống kê Metrics:** `http://127.0.0.1:5000/api/metrics`
# BMHTTT
