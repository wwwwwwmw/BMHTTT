import pypdf
import collections
import pandas as pd

reader = pypdf.PdfReader('tyaf019.pdf')
page13 = reader.pages[12]

elements = []
def visitor(text, cm, tm, font_dict, font_size):
    t = text.strip()
    if t:
        elements.append({'text': t, 'x': round(tm[4], 2), 'y': round(tm[5], 2)})

page13.extract_text(visitor_text=visitor)

# Define 14 themes with their approximate y centers
# We can find y clusters for the 14 themes
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

# Let's inspect all elements that are 'x' or digits in Total column
# Column xs:
# [22], [127], ... Total
headers = [el for el in elements if el['y'] < 85 and el['x'] >= 170]
headers.sort(key=lambda item: item['x'])

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

print(f"Detected {len(col_mapping)} columns:")
for x, name in col_mapping:
    print(f"x={x:.1f}: {name}")

# Now let's find the y centers for the 14 themes
# Let's check elements in the Total column (around x=486.8)
totals_in_pdf = [el for el in elements if abs(el['x'] - 486.8) < 4.0 and el['y'] > 85]
totals_in_pdf.sort(key=lambda item: item['y'])
print("\nTotals elements in PDF:")
for el in totals_in_pdf:
    print(f"y={el['y']}: {el['text']}")

# Let's find the y ranges for each of the 14 rows
# Each row has a total at the right end!
row_ys = [el['y'] for el in totals_in_pdf]
print("\nRow Ys count:", len(row_ys))
assert len(row_ys) == 14, f"Expected 14 row totals, found {len(row_ys)}"

# Let's pair row_ys with theme_names
theme_row_map = list(zip(theme_names, row_ys, [int(el['text']) for el in totals_in_pdf]))
for name, y, tot in theme_row_map:
    print(f"{name:35s}: y={y:.1f}, Reported Total={tot}")

# Now let's count 'x' in each cell
# For each paper col (first 37 columns)
paper_cols = col_mapping[:37]
matrix = {name: {p_name: 0 for _, p_name in paper_cols} for name in theme_names}

for el in elements:
    if el['text'] == 'x':
        # find matching col
        matched_col = None
        for cx, cname in paper_cols:
            if abs(cx - el['x']) < 4.0:
                matched_col = cname
                break
        # find matching row
        matched_row = None
        min_dy = 999
        for tname, ry, _ in theme_row_map:
            dy = abs(ry - el['y'])
            if dy < 15.0 and dy < min_dy:
                min_dy = dy
                matched_row = tname
        if matched_col and matched_row:
            matrix[matched_row][matched_col] = 1
        else:
            print(f"Unmatched x at x={el['x']}, y={el['y']} (matched_col={matched_col}, matched_row={matched_row})")

# Let's verify sum of x per row matches the reported total
print("\n--- VERIFICATION OF ROW TOTALS ---")
match_all = True
for name, ry, rep_tot in theme_row_map:
    calc_tot = sum(matrix[name].values())
    matches = (calc_tot == rep_tot)
    if not matches:
        match_all = False
    print(f"{name:35s}: Calculated={calc_tot:2d} | Paper Total={rep_tot:2d} | Match: {matches}")

print("All row totals match perfectly:", match_all)
