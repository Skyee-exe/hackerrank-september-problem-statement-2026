import os
import sys

# Ensure code folder is in path
code_dir = os.path.dirname(os.path.abspath(__file__))
if code_dir not in sys.path:
    sys.path.append(code_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from simulation.data_loader import DataLoader
from simulation.cash_flow import CashFlowSimulator
from simulation.decision_engine import DecisionEngine

def test_single_request(request_id):
    repo_root = os.path.dirname(code_dir)
    data_dir = os.path.join(repo_root, 'dataset')
    dl = DataLoader(data_dir=data_dir)
    sim = CashFlowSimulator(dl)
    engine = DecisionEngine(dl, sim)

    # Search in both sample_requests.csv and requests.csv
    req = None
    source = None
    for src_file in ['sample_requests.csv', 'requests.csv']:
        path = os.path.join(data_dir, src_file)
        if os.path.exists(path):
            import csv
            with open(path, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    if row['request_id'] == request_id:
                        req = row
                        source = src_file
                        break
        if req:
            break

    if not req:
        print(f"[-] Error: Request '{request_id}' not found in sample_requests.csv or requests.csv.")
        return

    user_id = req['user_id']
    profile = dl.profiles.get(user_id, {})
    curr = profile.get('home_currency', 'USD')
    bal = profile.get('current_available_balance', 0.0)
    min_b = profile.get('minimum_balance_to_keep', 0.0)
    req_amt = float(req['requested_amount'])

    print("=" * 70)
    print(f"[*] Testing Request: {request_id} (found in {source})")
    print("=" * 70)
    print(f"  User ID:                 {user_id}")
    print(f"  Available Balance:       {curr} {bal:,.2f}")
    print(f"  Minimum Balance Buffer:  {curr} {min_b:,.2f}")
    print(f"  Requested Amount:        {curr} {req_amt:,.2f} on {req['request_date']}")
    print(f"  Completion Deadline:     {req['desired_completion_date']}")
    print(f"  Category:                {req.get('request_category', 'General')}")
    print(f"  Description:             {req.get('request_description', '')}")

    # Available options
    opts = dl.payment_options_by_req.get(request_id, [])
    print(f"\nAvailable Payment Options ({len(opts)}):")
    for opt in opts:
        print(f"   - Option {opt['payment_option_id']}: {opt['payment_method']} | total: {opt['total_payable_amount']} | payments: {opt['number_of_payments']}")

    # Run decision
    pred = engine.evaluate_request(req)

    print("\n" + "-" * 70)
    print("AGENT DECISION OUTPUT:")
    print("-" * 70)
    print(f"Safe to Pay Today:              {curr} {pred['amount_safe_to_pay']:,.2f}")
    print(f"Affordability Status:           {pred['affordability_status']}")
    print(f"Recommended Payment Method:     {pred['recommended_payment_method']}")
    print(f"Payment Plan:                   {pred['payment_plan']}")
    print(f"Earliest Date For Full Payment: {pred['earliest_date_for_full_payment'] or 'None'}")
    print(f"Spending Changes Needed:        {pred['spending_changes_needed']}")
    print(f"Explanation:\n  \"{pred['decision_explanation']}\"")

    if source == 'sample_requests.csv':
        print("\n" + "-" * 70)
        print("GROUND TRUTH IN SAMPLE DATASET:")
        print("-" * 70)
        print(f"Actual Status:         {req['affordability_status']}")
        print(f"Actual Method:         {req['recommended_payment_method']}")
        print(f"Actual Plan:           {req['payment_plan']}")
        print(f"Actual Earliest Date:  {req['earliest_date_for_full_payment']}")
        print(f"Actual Changes:        {req['spending_changes_needed']}")
        print(f"Actual Explanation:\n  \"{req['decision_explanation']}\"")
    print("=" * 70)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python code/test_request.py <request_id>")
        print("Example: python code/test_request.py request_01")
        print("         python code/test_request.py request_26")
    else:
        test_single_request(sys.argv[1])
