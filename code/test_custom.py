import os
import sys
import argparse
from datetime import datetime, timedelta

# Ensure code directory is in sys.path
code_dir = os.path.dirname(os.path.abspath(__file__))
if code_dir not in sys.path:
    sys.path.append(code_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def parse_date(d_str):
    return datetime.strptime(d_str, '%Y-%m-%d').date()

def render_ascii_sparkline(daily_balances, min_buffer, req_date, days=90):
    """Renders a clean ASCII balance trend over the forecast horizon."""
    milestones = [req_date + timedelta(days=int(i * (days / 10))) for i in range(11)]
    vals = [daily_balances.get(d, 0.0) for d in milestones]
    min_v = min(min(vals), min_buffer * 0.8)
    max_v = max(max(vals), min_buffer * 1.5)
    span = max_v - min_v if max_v > min_v else 1.0

    print("\n📈 90-DAY BALANCE TRAJECTORY & SAFETY CUSHION:")
    print("   Balance (vs Emergency Buffer Line: ──────)")
    
    # 5-line height ASCII chart
    height = 5
    for row in range(height, -1, -1):
        threshold = min_v + (row / height) * span
        line_chars = []
        is_buffer_row = abs(threshold - min_buffer) <= (span / (height * 2))
        
        prefix = f"{threshold:>9,.0f} │" if not is_buffer_row else f" BUFFER │"
        for v in vals:
            if v >= threshold:
                line_chars.append("█")
            else:
                line_chars.append("─" if is_buffer_row else " ")
        print(f"   {prefix} {'  '.join(line_chars)}")
    print("             └" + "──" * 16)
    labels = [f"D{int(i * (days / 10)):02d}" for i in range(11)]
    print(f"              {' '.join(labels)}")

def simulate_advanced(
    balance,
    min_buffer,
    purchase_amount,
    purchase_date_str="2026-09-15",
    salary_amount=3000.0,
    salary_day=15,
    rent_amount=1200.0,
    rent_day=1,
    currency="$"
):
    req_date = parse_date(purchase_date_str)

    print("\n" + "═" * 78)
    print(f" 🚀 FINANCIAL DECISION SIMULATION: {currency}{purchase_amount:,.2f} Purchase")
    print("═" * 78)
    print(f"  Account Balance:  {currency}{balance:,.2f}     Emergency Cushion: {currency}{min_buffer:,.2f}")
    print(f"  Monthly Salary:   {currency}{salary_amount:,.2f} (Day {salary_day})     Monthly Rent:      {currency}{rent_amount:,.2f} (Day {rent_day})")
    print("─" * 78)

    def run_cash_ledger(extra_payments=None, salary_delay_days=0, emergency_shock=0.0):
        cur_bal = balance - emergency_shock
        lowest_bal = cur_bal
        daily = {}
        for day_offset in range(91):
            cur_date = req_date + timedelta(days=day_offset)

            # Purchase payments
            if extra_payments and cur_date in extra_payments:
                cur_bal -= extra_payments[cur_date]

            # Salary credit (with optional delay)
            effective_salary_day = salary_day + salary_delay_days
            if salary_amount > 0 and cur_date.day == (effective_salary_day % 28 or 28) and cur_date > req_date:
                cur_bal += salary_amount

            # Rent deduction
            if rent_amount > 0 and cur_date.day == rent_day and cur_date > req_date:
                cur_bal -= rent_amount

            daily[cur_date] = cur_bal
            if cur_bal < lowest_bal:
                lowest_bal = cur_bal

        return lowest_bal, daily

    # 1. Base Simulations
    upfront_min, upfront_daily = run_cash_ledger({req_date: purchase_amount})
    
    inst_dates = [req_date, req_date + timedelta(days=30), req_date + timedelta(days=60)]
    inst_pmt = round(purchase_amount / 3.0, 2)
    inst_min, inst_daily = run_cash_ledger({d: inst_pmt for d in inst_dates})

    # Find earliest safe single payment date
    earliest_safe_date = None
    for day_offset in range(91):
        test_date = req_date + timedelta(days=day_offset)
        min_bal, _ = run_cash_ledger({test_date: purchase_amount})
        if min_bal >= min_buffer - 0.01:
            earliest_safe_date = test_date
            break

    # Breakeven date: when does balance recover to original starting balance?
    breakeven_date = None
    active_daily = upfront_daily if upfront_min >= min_buffer else inst_daily
    for d, b in sorted(active_daily.items()):
        if d > req_date and b >= balance:
            breakeven_date = d
            break

    # Determine Optimal Recommendation
    if upfront_min >= min_buffer - 0.01:
        status = "affordable_now"
        method = "full_payment"
        plan = f"{purchase_date_str}:{purchase_amount:g}"
        active_min = upfront_min
        chosen_daily = upfront_daily
        explanation = f"Safe to pay in full today. Your balance will stay at least {currency}{upfront_min:,.2f}, remaining safely above your {currency}{min_buffer:,.2f} cushion."
    elif inst_min >= min_buffer - 0.01:
        status = "affordable_with_plan"
        method = "installments"
        plan = "|".join([f"{d.strftime('%Y-%m-%d')}:{inst_pmt:g}" for d in inst_dates])
        active_min = inst_min
        chosen_daily = inst_daily
        explanation = f"Use 3 installments of {currency}{inst_pmt:,.2f}/mo. Spreading the cost maintains a minimum balance of {currency}{inst_min:,.2f}, keeping your cushion protected."
    elif earliest_safe_date:
        status = "affordable_later"
        method = "wait"
        plan = f"{earliest_safe_date.strftime('%Y-%m-%d')}:{purchase_amount:g}"
        active_min = upfront_min
        chosen_daily = upfront_daily
        explanation = f"Wait until {earliest_safe_date.strftime('%d %B %Y')} for your confirmed salary. Buying today would crash your balance to {currency}{upfront_min:,.2f} (violating cushion)."
    else:
        status = "not_affordable"
        method = "not_recommended"
        plan = "none"
        active_min = upfront_min
        chosen_daily = upfront_daily
        explanation = f"Do not purchase. Drains your account below your {currency}{min_buffer:,.2f} safety buffer across all 90 days."

    # Render Visual ASCII Chart
    render_ascii_sparkline(chosen_daily, min_buffer, req_date)

    # 2. Advanced Stress Tests
    # Stress Test A: 7-day salary delay
    active_pmts = {req_date: purchase_amount} if method == "full_payment" else ({d: inst_pmt for d in inst_dates} if method == "installments" else {})
    stress_salary_min, _ = run_cash_ledger(active_pmts, salary_delay_days=7)
    
    # Stress Test B: $300 unexpected emergency expense shock
    stress_shock_min, _ = run_cash_ledger(active_pmts, emergency_shock=300.0)

    # Safety Health Score (0 - 100)
    if active_min < min_buffer:
        health_score = max(0, int((active_min / min_buffer) * 50))
    else:
        margin = active_min - min_buffer
        health_score = min(100, int(50 + (margin / (min_buffer + 1e-5)) * 50))

    score_badge = "🟢 ROBUST" if health_score >= 80 else ("🟡 MODERATE" if health_score >= 50 else "🔴 HIGH RISK")

    print("\n" + "─" * 78)
    print("📊 DECISION & ADVANCED FINANCIAL METRICS:")
    print("─" * 78)
    print(f"  • Recommendation:        {method.upper()} ({status})")
    print(f"  • Payment Plan:          {plan}")
    print(f"  • Financial Health Score:{health_score}/100 [{score_badge}]")
    print(f"  • Lowest Buffer Margin:  +{currency}{max(0, active_min - min_buffer):,.2f} above cushion")
    if breakeven_date:
        recovery_days = (breakeven_date - req_date).days
        print(f"  • Full Capital Recovery: {breakeven_date.strftime('%d %b %Y')} ({recovery_days} days to pre-purchase balance)")
    else:
        print(f"  • Full Capital Recovery: > 90 days")

    print("\n🔬 RESILIENCE STRESS-TESTS:")
    stress_a_status = "✅ PASS" if stress_salary_min >= min_buffer else "⚠️ AT RISK"
    stress_b_status = "✅ PASS" if stress_shock_min >= min_buffer else "⚠️ AT RISK"
    print(f"  1. 7-Day Paycheck Delay Shock:   Lowest {currency}{stress_salary_min:,.2f}  [{stress_a_status}]")
    print(f"  2. Unexpected $300 Emergency:    Lowest {currency}{stress_shock_min:,.2f}  [{stress_b_status}]")

    print("\n💡 PLAIN-ENGLISH SUMMARY:")
    print(f"  \"{explanation}\"")
    print("═" * 78 + "\n")

def main():
    # If user provided 3 simple positional arguments: python code/test_custom.py <balance> <buffer> <amount>
    if len(sys.argv) == 4 and not sys.argv[1].startswith('-'):
        try:
            bal = float(sys.argv[1])
            buf = float(sys.argv[2])
            amt = float(sys.argv[3])
            simulate_advanced(balance=bal, min_buffer=buf, purchase_amount=amt)
            return
        except ValueError:
            pass

    parser = argparse.ArgumentParser(description="Advanced, simplified financial test case simulator.")
    parser.add_argument('--balance', type=float, default=None, help="Current available bank balance")
    parser.add_argument('--buffer', type=float, default=None, help="Minimum balance cushion to keep")
    parser.add_argument('--amount', type=float, default=None, help="Purchase amount requested")
    parser.add_argument('--salary', type=float, default=3000.0, help="Monthly salary (default: 3000)")
    parser.add_argument('--payday', type=int, default=15, help="Payday date of month (default: 15)")
    parser.add_argument('--rent', type=float, default=1200.0, help="Monthly rent/bills (default: 1200)")
    parser.add_argument('--rent-day', type=int, default=1, help="Day rent is due (default: 1)")
    parser.add_argument('--currency', type=str, default="$", help="Currency symbol (default: $)")

    args = parser.parse_args()

    if args.balance is not None and args.buffer is not None and args.amount is not None:
        simulate_advanced(
            balance=args.balance,
            min_buffer=args.buffer,
            purchase_amount=args.amount,
            salary_amount=args.salary,
            salary_day=args.payday,
            rent_amount=args.rent,
            rent_day=args.rent_day,
            currency=args.currency
        )
    else:
        # Interactive terminal mode: ask user to put in values
        print("=" * 78)
        print(" 💬 INTERACTIVE FINANCIAL TEST WIZARD")
        print(" Enter your financial details below (or press Enter for defaults):")
        print("=" * 78)
        try:
            val = input("1. Current bank balance (e.g. 5000): ").strip()
            bal = float(val) if val else 5000.0

            val = input("2. Minimum emergency cushion to keep (e.g. 1000): ").strip()
            buf = float(val) if val else 1000.0

            val = input("3. Purchase price of the item (e.g. 1200): ").strip()
            amt = float(val) if val else 1200.0

            val = input("4. Monthly salary [default 3000]: ").strip()
            sal = float(val) if val else 3000.0

            val = input("5. Salary payday of the month (1-31) [default 15]: ").strip()
            pday = int(val) if val else 15

            val = input("6. Monthly rent / essential bills [default 1200]: ").strip()
            rnt = float(val) if val else 1200.0

            val = input("7. Rent due day of the month (1-31) [default 1]: ").strip()
            rday = int(val) if val else 1

            simulate_advanced(
                balance=bal,
                min_buffer=buf,
                purchase_amount=amt,
                salary_amount=sal,
                salary_day=pday,
                rent_amount=rnt,
                rent_day=rday,
                currency="$"
            )
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled. Running with sample defaults:\n")
            simulate_advanced(
                balance=5000.0,
                min_buffer=1000.0,
                purchase_amount=1200.0,
                salary_amount=3000.0,
                salary_day=15,
                rent_amount=1200.0,
                rent_day=1,
                currency="$"
            )

if __name__ == '__main__':
    main()
