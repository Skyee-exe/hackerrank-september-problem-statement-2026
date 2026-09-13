import os
import sys
import csv

# Add code directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.dirname(current_dir)
sys.path.append(code_dir)

from simulation.data_loader import DataLoader
from simulation.cash_flow import CashFlowSimulator
from simulation.decision_engine import DecisionEngine

def evaluate():
    print("=" * 60)
    print("Evaluating Buy or Wait Decision Agent on Sample Requests")
    print("=" * 60)

    repo_root = os.path.dirname(code_dir)
    sample_path = os.path.join(repo_root, 'dataset', 'sample_requests.csv')
    
    if not os.path.exists(sample_path):
        print(f"Error: {sample_path} not found.")
        return

    dl = DataLoader(data_dir=os.path.join(repo_root, 'dataset'))
    sim = CashFlowSimulator(dl)
    engine = DecisionEngine(dl, sim)

    with open(sample_path, 'r', encoding='utf-8') as f:
        samples = list(csv.DictReader(f))

    total = len(samples)
    matches = {
        'status': 0,
        'method': 0,
        'earliest_date': 0,
        'spending_changes': 0
    }

    for s in samples:
        req_id = s['request_id']
        pred = engine.evaluate_request(s)

        status_match = pred['affordability_status'] == s['affordability_status']
        method_match = pred['recommended_payment_method'] == s['recommended_payment_method']
        date_match = pred['earliest_date_for_full_payment'] == s['earliest_date_for_full_payment']
        changes_match = pred['spending_changes_needed'] == s['spending_changes_needed']

        if status_match: matches['status'] += 1
        if method_match: matches['method'] += 1
        if date_match: matches['earliest_date'] += 1
        if changes_match: matches['spending_changes'] += 1

        mark = "OK  " if (status_match and method_match) else "FAIL"
        print(f"[{mark}] {req_id}: Status: pred={pred['affordability_status']:19} actual={s['affordability_status']:19} | Method: pred={pred['recommended_payment_method']:15} actual={s['recommended_payment_method']:15}")

    print("\n" + "=" * 60)
    print("Summary Performance:")
    print(f"  Affordability Status Accuracy: {matches['status']}/{total} ({matches['status']/total*100:.1f}%)")
    print(f"  Payment Method Accuracy:       {matches['method']}/{total} ({matches['method']/total*100:.1f}%)")
    print(f"  Earliest Date Match:           {matches['earliest_date']}/{total} ({matches['earliest_date']/total*100:.1f}%)")
    print(f"  Spending Changes Match:        {matches['spending_changes']}/{total} ({matches['spending_changes']/total*100:.1f}%)")
    print("=" * 60)

if __name__ == '__main__':
    evaluate()
