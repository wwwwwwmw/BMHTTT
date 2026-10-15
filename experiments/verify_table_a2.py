import pandas as pd
import sys

def verify_table_a2(csv_path="docs/reproducibility_review.csv"):
    df = pd.read_csv(csv_path)
    
    # 37 papers + 1 total row = 38 rows
    assert len(df) == 38, f"Expected 38 rows, got {len(df)}"
    
    paper_rows = df[df['paper_id'] != 'TOTAL']
    total_row = df[df['paper_id'] == 'TOTAL'].iloc[0]
    
    expected_totals = {
        "Case-focused": 19,
        "Competence": 27,
        "Confidentiality": 13,
        "Ease of use": 15,
        "Feedback": 18,
        "Impunity": 28,
        "Independence": 6,
        "Integration": 12,
        "Management support": 18,
        "Shared ownership and accountability": 9,
        "Speed and adaptivity": 8,
        "Standardization": 19,
        "System orientation": 9,
        "Voluntariness": 8
    }
    
    print("=" * 70)
    print("REPRODUCIBILITY VERIFICATION: Table A2 vs. Extracted Review CSV")
    print("=" * 70)
    print(f"{'Design Theme':36s} | {'Calculated':10s} | {'Target Table A2':15s} | Status")
    print("-" * 70)
    
    all_matched = True
    for theme, target in expected_totals.items():
        calc = int(paper_rows[theme].sum())
        csv_tot = int(total_row[theme])
        matched = (calc == target == csv_tot)
        if not matched:
            all_matched = False
        print(f"{theme:36s} | {calc:10d} | {target:15d} | {'PASS' if matched else 'FAIL'}")
    
    print("-" * 70)
    domain_counts = paper_rows['domain'].value_counts().to_dict()
    print(f"Domain distribution: Healthcare={domain_counts.get('Healthcare', 0)}, Aviation={domain_counts.get('Aviation', 0)} (Total={len(paper_rows)})")
    
    if all_matched and domain_counts.get('Healthcare', 0) == 33 and domain_counts.get('Aviation', 0) == 4:
        print("\n>>> REPRODUCIBILITY VERIFICATION SUCCESS: 100% MATCH WITH PAPER TABLE A2 <<<")
        return True
    else:
        print("\n>>> REPRODUCIBILITY VERIFICATION FAILED <<<")
        sys.exit(1)

if __name__ == "__main__":
    verify_table_a2()
