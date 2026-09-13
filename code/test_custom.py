import os
import sys
import argparse
from datetime import datetime, timedelta

# Ensure code path is available
code_dir = os.path.dirname(os.path.abspath(__file__))
if code_dir not in sys.path:
    sys.path.append(code_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def parse_date(d_str):
    return datetime.strptime(d_str, '%Y-%m-%d').date()

def simulate_custom_scenario(
    balance,
    min_buffer,
    purchase_amount,
    purchase_date_str,
    salary_amount=0.0,
    salary_day=15,
    bills=None,
    currency="USD",
    installments_available=True
):
    """
    Simulates any arbitrary custom test case over 90 days.
    bills: list of dicts [{'name': 'Rent', 'amount': 1200, 'day': 1}]
    """
    if bills is None:
        bills = []

    req_date = parse_date(purchase_date_str)

    print("=" * 75)
    print(" 🧪 CUSTOM TEST CASE SIMULATION")
    print("=" * 75)
    print(f"  Starting Balance:        {currency} {balance:,.2f}")
    print(f"  Emergency Safety Buffer: {currency} {min_buffer:,.2f}")
    print(f"  Monthly Salary:          {currency} {salary_amount:,.2f} on Day {salary_day} of each month")
    print(f"  Recurring Bills:")
    for b in bills:
        print(f"    • {b['name']}: {currency} {b['amount']:,.2f} on Day {b['day']}")
    print(f"  Requested Purchase:      {currency} {purchase_amount:,.2f} on {purchase_date_str}")
    print("-" * 75)

    def run_sim(extra_payments=None):
        cur_bal = balance
        lowest_bal = cur_bal
        daily = {}
        for day_offset in range(91):
            cur_date = req_date + timedelta(days=day_offset)

            # Deduct purchase payments
            if extra_payments and cur_date in extra_payments:
                cur_bal -= extra_payments[cur_date]

            # Add regular salary
            if salary_amount > 0 and cur_date.day == salary_day and cur_date > req_date:
                cur_bal += salary_amount

            # Deduct bills
            for b in bills:
                if cur_date.day == b['day'] and cur_date > req_date:
                    cur_bal -= b['amount']

            daily[cur_date] = cur_bal
            if cur_bal < lowest_bal:
                lowest_bal = cur_bal

        return lowest_bal, daily

    # 1. Test Baseline (No purchase)
    base_min, _ = run_sim()

    # 2. Test Upfront Payment Today
    upfront_min, upfront_daily = run_sim({req_date: purchase_amount})

    # 3. Test 3-Month Installment Plan (3 equal monthly payments)
    inst_dates = [req_date, req_date + timedelta(days=30), req_date + timedelta(days=60)]
    inst_pmt = round(purchase_amount / 3.0, 2)
    inst_payments = {d: inst_pmt for d in inst_dates}
    inst_min, inst_daily = run_sim(inst_payments)

    # 4. Find Earliest Safe Payday
    earliest_safe_date = None
    for day_offset in range(91):
        test_date = req_date + timedelta(days=day_offset)
        min_if_paid, _ = run_sim({test_date: purchase_amount})
        if min_if_paid >= min_buffer - 0.01:
            earliest_safe_date = test_date
            break

    # Decision Engine Logic
    print("\nAGENT EVALUATION & DECISION:")
    print("-" * 75)

    if upfront_min >= min_buffer - 0.01:
        status = "affordable_now"
        method = "full_payment"
        plan = f"{purchase_date_str}:{purchase_amount:g}"
        earliest_d = purchase_date_str
        explanation = f"Pay {currency} {purchase_amount:,.2f} today in full. Balance stays at least {currency} {upfront_min:,.2f} (above {currency} {min_buffer:,.2f} buffer)."
    elif installments_available and inst_min >= min_buffer - 0.01:
        status = "affordable_with_plan"
        method = "installments"
        plan = "|".join([f"{d.strftime('%Y-%m-%d')}:{inst_pmt:g}" for d in inst_dates])
        earliest_d = earliest_safe_date.strftime('%Y-%m-%d') if earliest_safe_date else "None"
        explanation = f"Use 3 installments of {currency} {inst_pmt:,.2f}. Spreading the cost keeps your lowest balance at {currency} {inst_min:,.2f}, safely above your buffer."
    elif earliest_safe_date:
        status = "affordable_later"
        method = "wait"
        plan = f"{earliest_safe_date.strftime('%Y-%m-%d')}:{purchase_amount:g}"
        earliest_d = earliest_safe_date.strftime('%Y-%m-%d')
        explanation = f"Wait until {earliest_safe_date.strftime('%d %B %Y')} when salary arrives. Paying today would crash your balance to {currency} {upfront_min:,.2f} (below buffer)."
    else:
        status = "not_affordable"
        method = "not_recommended"
        plan = "none"
        earliest_d = "None"
        explanation = f"Do not purchase. None of the available options protect your {currency} {min_buffer:,.2f} emergency safety buffer."

    print(f"  • Affordability Status:       {status}")
    print(f"  • Recommended Method:         {method}")
    print(f"  • Payment Schedule:           {plan}")
    print(f"  • Earliest Full Payment Date: {earliest_d}")
    print(f"  • Decision Explanation:")
    print(f"    \"{explanation}\"")
    print("=" * 75 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Test any custom financial test case.")
    parser.add_argument('--balance', type=float, default=None, help="Current available bank balance")
    parser.add_argument('--buffer', type=float, default=None, help="Minimum balance cushion to keep")
    parser.add_argument('--amount', type=float, default=None, help="Purchase amount requested")
    parser.add_argument('--date', type=str, default="2026-09-15", help="Purchase date YYYY-MM-DD")
    parser.add_argument('--salary', type=float, default=3000.0, help="Monthly salary amount")
    parser.add_argument('--payday', type=int, default=15, help="Day of month salary arrives (1-31)")
    parser.add_argument('--rent', type=float, default=1200.0, help="Monthly rent amount")
    parser.add_argument('--rent-day', type=int, default=1, help="Day of month rent is due (1-31)")
    parser.add_argument('--currency', type=str, default="USD", help="Currency code")

    args = parser.parse_args()

    # If flags provided, run directly
    if args.balance is not None and args.buffer is not None and args.amount is not None:
        bills = [{'name': 'Rent', 'amount': args.rent, 'day': args.rent_day}] if args.rent > 0 else []
        simulate_custom_scenario(
            balance=args.balance,
            min_buffer=args.buffer,
            purchase_amount=args.amount,
            purchase_date_str=args.date,
            salary_amount=args.salary,
            salary_day=args.payday,
            bills=bills,
            currency=args.currency
        )
    else:
        # Default demo scenario
        print("💡 Tip: You can pass custom flags, or test this demo scenario:\n")
        bills = [{'name': 'Rent', 'amount': 1200.0, 'day': 1}]
        simulate_custom_scenario(
            balance=4000.0,
            min_buffer=1000.0,
            purchase_amount=800.0,
            purchase_date_str="2026-09-15",
            salary_amount=3000.0,
            salary_day=15,
            bills=bills,
            currency="USD"
        )
        print("To run your own test case:")
        print("  python code/test_custom.py --balance 5000 --buffer 1000 --amount 1500 --salary 3500 --rent 1400\n")

if __name__ == '__main__':
    main()
