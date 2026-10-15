import pypdf
import re
import csv
import pandas as pd

# 1. Read PDF and get references
with open('docs/extracted_paper_text.txt', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('References')
ref_text = text[pos:]

matches = list(re.finditer(r'(?:^|\n|\s)(\d+)\.\s+([A-Z][^\n]+)', ref_text))
refs = {}
for i in range(len(matches)):
    num = int(matches[i].group(1))
    start = matches[i].start(2)
    end = matches[i+1].start() if i + 1 < len(matches) else len(ref_text)
    content = ref_text[start:end].replace('\n', ' ').strip()
    refs[num] = re.sub(r'\s+', ' ', content)

paper_ids = [22, 127, 129, 163, 83, 95, 33, 169, 113, 93, 23, 165, 170, 171, 172, 107, 173, 130, 94, 146, 147, 92, 36, 84, 118, 81, 174, 164, 175, 102, 176, 177, 178, 108, 26, 82, 117]

# 2. Extract matrix from Table A2 on page 13
reader = pypdf.PdfReader('tyaf019.pdf')
page13 = reader.pages[12]

elements = []
def visitor(text, cm, tm, font_dict, font_size):
    t = text.strip()
    if t:
        elements.append({'text': t, 'x': round(tm[4], 2), 'y': round(tm[5], 2)})
page13.extract_text(visitor_text=visitor)

theme_names = [
    "Case-focused",
    "Competence",
    "Confidentiality",
    "Ease of use",
    "Feedback",
    "Impunity",
    "Independence",
    "Integration",
    "Management support",
    "Shared ownership and accountability",
    "Speed and adaptivity",
    "Standardization",
    "System orientation",
    "Voluntariness"
]

totals_in_pdf = [el for el in elements if abs(el['x'] - 486.8) < 4.0 and el['y'] > 85]
totals_in_pdf.sort(key=lambda item: item['y'])
row_ys = [el['y'] for el in totals_in_pdf]
theme_row_map = list(zip(theme_names, row_ys, [int(el['text']) for el in totals_in_pdf]))

# Detect columns
headers = [el for el in elements if el['y'] < 85 and el['x'] >= 170]
headers.sort(key=lambda item: item['x'])

import collections
cols = collections.defaultdict(list)
for el in headers:
    matched = None
    for k in cols:
        if abs(k - el['x']) < 3.0:
            matched = k
            break
    if matched is None:
        cols[el['x']].append(el)
    else:
        cols[matched].append(el)

col_mapping = []
for k in sorted(cols.keys()):
    txt = ''.join([item['text'] for item in cols[k]]).replace('[', '').replace(']', '').strip()
    col_mapping.append((k, txt))

paper_cols = col_mapping[:37]

# matrix[theme][pid]
matrix = {name: {int(p_name): 0 for _, p_name in paper_cols} for name in theme_names}

for el in elements:
    if el['text'] == 'x':
        matched_col = None
        for cx, cname in paper_cols:
            if abs(cx - el['x']) < 4.0:
                matched_col = int(cname)
                break
        matched_row = None
        min_dy = 999
        for tname, ry, _ in theme_row_map:
            dy = abs(ry - el['y'])
            if dy < 15.0 and dy < min_dy:
                min_dy = dy
                matched_row = tname
        if matched_col and matched_row:
            matrix[matched_row][matched_col] = 1

aviation_ids = {95, 33, 169, 102}

# Build rows for reproducibility_review.csv
csv_rows = []
for pid in paper_ids:
    full_ref = refs.get(pid, "")
    domain = "Aviation" if pid in aviation_ids else "Healthcare"
    
    # Try parsing authors and title
    # e.g. Ahluwalia J, Marriott L. Critical incident reporting systems. Semin Fetal Neonatal Med 2005; 10 :31–7.
    parts = full_ref.split('. ')
    authors = parts[0] if len(parts) > 0 else full_ref
    title = parts[1] if len(parts) > 1 else ""
    venue = '. '.join(parts[2:]) if len(parts) > 2 else ""

    row = {
        "paper_id": pid,
        "domain": domain,
        "authors": authors,
        "title": title,
        "citation": full_ref
    }
    for t in theme_names:
        row[t] = matrix[t][pid]
    csv_rows.append(row)

# Add Total row
total_row = {
    "paper_id": "TOTAL",
    "domain": "-",
    "authors": "-",
    "title": "Total papers per theme (Target: Table A2)",
    "citation": "-"
}
for t, _, rep_tot in theme_row_map:
    total_row[t] = sum(r[t] for r in csv_rows)
csv_rows.append(total_row)

df = pd.DataFrame(csv_rows)
df.to_csv('docs/reproducibility_review.csv', index=False, encoding='utf-8-sig')
print("Saved docs/reproducibility_review.csv successfully!")
