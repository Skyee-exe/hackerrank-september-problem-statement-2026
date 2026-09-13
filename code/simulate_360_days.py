import os
import sys
from datetime import datetime, timedelta

# Ensure code directory is in sys.path
code_dir = os.path.dirname(os.path.abspath(__file__))
if code_dir not in sys.path:
    sys.path.append(code_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from simulation.data_loader import DataLoader
from simulation.cash_flow import CashFlowSimulator, parse_date
from simulation.decision_engine import DecisionEngine

def run_360_day_simulation(request_id):
    repo_root = os.path.dirname(code_dir)
    data_dir = os.path.join(repo_root, 'dataset')
    dl = DataLoader(data_dir=data_dir)
    sim = CashFlowSimulator(dl)
    engine = DecisionEngine(dl, sim)

    # Search for request in sample_requests.csv or requests.csv
    import csv
    req = None
    source = None
    for src_file in ['sample_requests.csv', 'requests.csv']:
        path = os.path.join(data_dir, src_file)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    if row['request_id'] == request_id:
                        req = row
                        source = src_file
                        break
        if req:
            break

    if not req:
        print(f"[-] Error: Request '{request_id}' not found.")
        return

    user_id = req['user_id']
    profile = dl.profiles.get(user_id, {})
    curr = profile.get('home_currency', 'USD')
    bal = profile.get('current_available_balance', 0.0)
    min_b = profile.get('minimum_balance_to_keep', 0.0)
    req_amt = float(req['requested_amount'])
    req_date_str = req['request_date']
    req_date = parse_date(req_date_str)

    print("=" * 80)
    print(f" 360-DAY (12-MONTH) CASH FLOW SIMULATION: {request_id}")
    print("=" * 80)
    print(f"User ID:                 {user_id}")
    print(f"Starting Balance:        {curr} {bal:,.2f}")
    print(f"Safety Cushion Buffer:   {curr} {min_b:,.2f}")
    print(f"Requested Purchase:      {curr} {req_amt:,.2f} on {req_date_str}")
    print(f"Completion Deadline:     {req['desired_completion_date']}")

    # Decision Engine result (standard 90-day evaluation)
    decision = engine.evaluate_request(req)
    print("\n" + "-" * 80)
    print(f"AGENT RECOMMENDATION (Based on Rules):")
    print(f"  • Affordability: {decision['affordability_status']}")
    print(f"  • Method:        {decision['recommended_payment_method']}")
    print(f"  • Plan:          {decision['payment_plan']}")
    print(f"  • Explanation:   {decision['decision_explanation']}")
    print("-" * 80)

    # Parse recommended plan payments into a dictionary {date: amount}
    plan_payments = {}
    if decision['payment_plan'] and decision['payment_plan'] != 'none':
        for chunk in decision['payment_plan'].split('|'):
            if ':' in chunk:
                d_str, a_str = chunk.split(':')
                try:
                    plan_payments[parse_date(d_str)] = float(a_str)
                except ValueError:
                    pass

    # Upfront payment test: {req_date: req_amt}
    upfront_payment = {req_date: req_amt}

    # 1. Baseline 360-Day Simulation (No purchase)
    base_min, base_daily = sim.simulate(user_id, req_date_str, horizon_days=360)

    # 2. Plan 360-Day Simulation (With recommended plan)
    plan_min, plan_daily = sim.simulate(user_id, req_date_str, extra_payments=plan_payments, horizon_days=360)

    # 3. Upfront 360-Day Simulation (If paid 100% upfront today)
    upfront_min, upfront_daily = sim.simulate(user_id, req_date_str, extra_payments=upfront_payment, horizon_days=360)

    print("\nMONTH-BY-MONTH 360-DAY BALANCE TRAJECTORY:")
    print("┌───────┬────────────┬──────────────────┬──────────────────┬──────────────────┬───────────┐")
    print("│ Month │    Date    │ Baseline Balance │ With Rec. Plan   │ If Paid Upfront  │ Cushion?  │")
    print("├───────┼────────────┼──────────────────┼──────────────────┼──────────────────┼───────────┤")

    milestones = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
    for i, offset in enumerate(milestones):
        d = req_date + timedelta(days=offset)
        b_base = base_daily.get(d, 0.0)
        b_plan = plan_daily.get(d, 0.0)
        b_up = upfront_daily.get(d, 0.0)

        # Safety tag for recommended plan
        if b_plan >= min_b:
            tag = " [SAFE] "
        else:
            diff = min_b - b_plan
            tag = f" [-{curr} {diff:,.0f}]"

        m_label = f"Day {offset:3d}" if offset > 0 else "Start  "
        print(f"│ {m_label} │ {d.strftime('%Y-%m-%d')} │ {curr:>3} {b_base:>12,.2f} │ {curr:>3} {b_plan:>12,.2f} │ {curr:>3} {b_up:>12,.2f} │{tag:^11}│")

    print("└───────┴────────────┴──────────────────┴──────────────────┴──────────────────┴───────────┘")

    print("\n" + "=" * 80)
    print(" 360-DAY SUMMARY INSIGHTS:")
    print("=" * 80)
    print(f"1. Minimum Balance Reached Over 360 Days:")
    print(f"   • Baseline (No purchase):    {curr} {base_min:,.2f} (Buffer: {curr} {min_b:,.2f})")
    print(f"   • With Recommended Plan:     {curr} {plan_min:,.2f} {'[PROTECTED]' if plan_min >= min_b else '[BREACHED]'}")
    print(f"   • If Paid 100% Upfront:      {curr} {upfront_min:,.2f} {'[SAFE]' if upfront_min >= min_b else '[UNSAFE - DIPS BELOW BUFFER]'}")

    if upfront_min < min_b and plan_min >= min_b:
        print(f"\n💡 KEY TAKEAWAY:")
        print(f"   Paying upfront would have crashed the account buffer to {curr} {upfront_min:,.2f}.")
        print(f"   The recommended plan successfully navigated cash flow across all 360 days!")
    elif plan_min >= min_b:
        print(f"\n💡 KEY TAKEAWAY:")
        print(f"   The user's cash flow is healthy and sustainable across the full 360-day horizon.")
    else:
        print(f"\n💡 KEY TAKEAWAY:")
        print(f"   Long-term commitments exceed projected income over 360 days; spending adjustments needed.")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'request_30'
    run_360_day_simulation(target)
