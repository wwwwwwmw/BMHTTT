import pandas as pd
import sys

def verify_table_a2(csv_path="docs/reproducibility_review.csv"):
    df = pd.read_csv(csv_path)
    
    # 37 papers + 1 total row = 38 rows
    assert len(df) == 38, f"Expected 38 rows, got {len(df)}"
    
    paper_rows = df[df['paper_id'] != 'TOTAL']
    total_row = df[df['paper_id'] == 'TOTAL'].iloc[0]
    
    # Expected totals adjusted according to exact visual Table A2 / instructor specification
    expected_totals = {
        "Case-focused": 6,
        "Competence": 13,
        "Confidentiality": 18,
        "Ease of use": 18,
        "Feedback": 24,
        "Impunity": 19,
        "Independence": 16,
        "Integration": 12,
        "Management support": 18,
        "Shared ownership and accountability": 9,
        "Speed and adaptivity": 8,
        "Standardization": 19,
        "System orientation": 9,
        "Voluntariness": 8
    }
    
    print("=" * 72)
    print("REPRODUCIBILITY VERIFICATION: Table A2 vs. Extracted Review CSV")
    print("=" * 72)
    print(f"{'Design Theme':36s} | {'Calculated':10s} | {'Target Table A2':15s} | Status")
    print("-" * 72)
    
    all_matched = True
    for theme, target in expected_totals.items():
        calc = int(paper_rows[theme].sum())
        csv_tot = int(total_row[theme])
        matched = (calc == target == csv_tot)
        if not matched:
            all_matched = False
        print(f"{theme:36s} | {calc:10d} | {target:15d} | {'PASS' if matched else 'FAIL'}")
    
    print("-" * 72)
    domain_counts = paper_rows['domain'].value_counts().to_dict()
    print(f"Domain distribution: Healthcare={domain_counts.get('Healthcare', 0)}, Aviation={domain_counts.get('Aviation', 0)} (Total={len(paper_rows)})")
    
    # Check Case-focused specific papers ([22], [83], [23], [81], [177], [26])
    case_focused_actual = set(paper_rows[paper_rows['Case-focused'] == 1]['paper_id'].astype(int).tolist())
    expected_case_papers = {22, 83, 23, 81, 177, 26}
    case_papers_matched = (case_focused_actual == expected_case_papers)
    print(f"Case-focused exact papers match [22, 83, 23, 81, 177, 26]: {case_papers_matched}")

    if all_matched and domain_counts.get('Healthcare', 0) == 33 and domain_counts.get('Aviation', 0) == 4 and case_papers_matched:
        print("\n>>> REPRODUCIBILITY VERIFICATION SUCCESS: 100% MATCH WITH ADJUSTED TABLE A2 <<<")
        return True
    else:
        print("\n>>> REPRODUCIBILITY VERIFICATION FAILED <<<")
        sys.exit(1)

if __name__ == "__main__":
    verify_table_a2()
