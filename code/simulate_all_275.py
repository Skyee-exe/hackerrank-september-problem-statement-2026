import os
import sys
import csv
import time
from collections import Counter

# Ensure code folder is in path
code_dir = os.path.dirname(os.path.abspath(__file__))
if code_dir not in sys.path:
    sys.path.append(code_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from simulation.data_loader import DataLoader
from simulation.cash_flow import CashFlowSimulator
from simulation.decision_engine import DecisionEngine

def simulate_all_requests():
    repo_root = os.path.dirname(code_dir)
    data_dir = os.path.join(repo_root, 'dataset')

    print("=" * 75)
    print(" 🚀 SIMULATING ALL 275 REQUESTS (Samples 1-25 + Evaluation 26-275)")
    print("=" * 75)
    start_time = time.time()

    dl = DataLoader(data_dir=data_dir)
    sim = CashFlowSimulator(dl)
    engine = DecisionEngine(dl, sim)

    # 1. Load sample_requests.csv (25)
    all_requests = []
    samples_path = os.path.join(data_dir, 'sample_requests.csv')
    if os.path.exists(samples_path):
        with open(samples_path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                row['_source'] = 'sample'
                all_requests.append(row)

    # 2. Load requests.csv (250)
    requests_path = os.path.join(data_dir, 'requests.csv')
    if os.path.exists(requests_path):
        with open(requests_path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                row['_source'] = 'evaluation'
                all_requests.append(row)

    total_count = len(all_requests)
    print(f"Loaded {total_count} total requests ({len([r for r in all_requests if r['_source'] == 'sample'])} samples + {len([r for r in all_requests if r['_source'] == 'evaluation'])} evaluation).")
    print("Running 90-day cash flow simulation across all requests...\n")

    status_counts = Counter()
    method_counts = Counter()
    currency_counts = Counter()

    for i, req in enumerate(all_requests, 1):
        pred = engine.evaluate_request(req)
        status = pred['affordability_status']
        method = pred['recommended_payment_method']
        status_counts[status] += 1
        method_counts[method] += 1
        
        user_curr = dl.profiles.get(req['user_id'], {}).get('home_currency', 'USD')
        currency_counts[user_curr] += 1

        if i % 50 == 0 or i == total_count:
            print(f"  [Progress] Simulated {i:3d}/{total_count} requests ({i/total_count*100:.1f}%)")

    elapsed = time.time() - start_time
    print("-" * 75)
    print(f"⏱️  Completed all {total_count} simulations in {elapsed:.2f} seconds ({elapsed/total_count*1000:.2f} ms/request)!")
    print("=" * 75)
    
    print("\n📊 AFFORDABILITY STATUS DISTRIBUTION ACROSS ALL 275 REQUESTS:")
    for status, cnt in status_counts.most_common():
        pct = cnt / total_count * 100
        bar = "█" * int(pct / 2)
        print(f"  • {status:22}: {cnt:3d} ({pct:5.1f}%)  {bar}")

    print("\n💳 RECOMMENDED PAYMENT METHOD DISTRIBUTION:")
    for method, cnt in method_counts.most_common():
        pct = cnt / total_count * 100
        bar = "█" * int(pct / 2)
        print(f"  • {method:22}: {cnt:3d} ({pct:5.1f}%)  {bar}")

    print("\n🌍 CURRENCY DISTRIBUTION:")
    for curr, cnt in currency_counts.most_common():
        pct = cnt / total_count * 100
        print(f"  • {curr:5}: {cnt:3d} ({pct:5.1f}%)")

    print("\n" + "=" * 75)
    print("✅ All 275 requests were successfully simulated and decided!")
    print("=" * 75)

if __name__ == '__main__':
    simulate_all_requests()
