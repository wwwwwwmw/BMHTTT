# BÁO CÁO THỰC NGHIỆM ĐỐI CHỨNG HỆ THỐNG CYBER-IRS
**Dự án:** DT126-IRS-Repro | **Cơ sở lý thuyết:** DOI 10.1093/cybsec/tyaf019  
**Bài báo gốc:** *Learning from safety science: designing incident reporting systems in cybersecurity* (Nico Ebert et al., 2025)  
**Phương pháp:** 3 lần chạy thực nghiệm độc lập (Seeds: 42, 100, 2026) với kỹ thuật Cluster-stratified Resampling (85% test clusters) và Random Sequence Shuffling.

---

### 1. BẢNG TỔNG HỢP KẾT QUẢ THỰC NGHIỆM (3 RUNS & MEAN ± STD)

| Chỉ số Thực nghiệm (Metric) | Run 1 (Seed 42) | Run 2 (Seed 100) | Run 3 (Seed 2026) | Giá trị Trung bình (Mean ± Std) |
|---|---|---|---|---|
| **Số bản ghi mẫu (Sample Size)** | 115 | 115 | 117 | **115.7** |
| **De-duplication Precision** | 0.6000 | 0.6067 | 0.5978 | **0.6015 ± 0.0046** |
| **De-duplication Recall** | 0.7941 | 0.7941 | 0.7857 | **0.7913 ± 0.0048** |
| **De-duplication F1-Score** | 0.6835 | 0.6879 | 0.6790 | **0.6835 ± 0.0045** |
| **Tỷ lệ hoàn thành Form Dài (Baseline)** | 66.09% | 66.09% | 76.07% | **69.42 ± 5.76%** |
| **Tỷ lệ hoàn thành Form Ngắn (Variant)** | 94.78% | 93.04% | 95.73% | **94.52 ± 1.36%** |
| **Thời gian gửi Form Dài (Baseline)** | 183.4s | 181.37s | 180.19s | **181.65 ± 1.62s** |
| **Thời gian gửi Form Ngắn (Variant)** | 50.19s | 49.73s | 50.83s | **50.25 ± 0.55s** |
| **Thời gian Triage khi chưa gom trùng** | 5.75h | 5.75h | 5.85h | **5.78 ± 0.06h** |
| **Thời gian Triage sau khi khử trùng lặp** | 2.0h | 2.04h | 2.02h | **2.02 ± 0.02h** |
| **Tỷ lệ tiết kiệm thời gian Triage cho SOC** | 65.22% | 64.49% | 65.53% | **65.08 ± 0.53%** |
| **Tỷ lệ che PII thành công (Data Minimization)** | 100.0% | 100.0% | 100.0% | **100.00 ± 0.00%** |

---

### 2. PHÂN TÍCH KẾT QUẢ ĐỐI CHỨNG VỚI NGUYÊN LÝ BÀI BÁO GỐC

1. **Ease of Use vs. Standardization (Chủ đề #4 & #12):**
   - Form ngắn đạt tỷ lệ hoàn thành trung bình **94.52 ± 1.36%**, vượt trội so với **69.42 ± 5.76%** của Form dài.
   - Thời gian gửi báo cáo giảm hơn 70% từ **181.65 ± 1.62s** xuống **50.25 ± 0.55s**, chứng minh hệ thống đã hóa giải mâu thuẫn giữa tính thân thiện người dùng và chuẩn hóa dữ liệu.

2. **Speed & Adaptivity qua De-duplication (Chủ đề #11):**
   - Module khử trùng lặp (TF-IDF + RapidFuzz) đạt **F1-Score = 0.6835 ± 0.0045** (Recall = 0.7913 ± 0.0048), giảm tải trung bình **65.08 ± 0.53%** thời gian hàng đợi SOC.

3. **Confidentiality & Impunity (Chủ đề #3 & #6):**
   - Bộ lọc PII Masking che thành công **100.00 ± 0.00%** dữ liệu nhạy cảm trước khi lưu DB.
   - Cơ chế Tracking Token ẩn danh cho phép người dùng nhận phản hồi và học tập mà hoàn toàn bảo mật danh tính.
