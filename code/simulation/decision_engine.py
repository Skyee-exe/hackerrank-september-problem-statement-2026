import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.append('code')
from simulation.data_loader import DataLoader
from simulation.cash_flow import CashFlowSimulator
from simulation.explanation import generate_explanation

def parse_date(d_str):
    return datetime.strptime(d_str, '%Y-%m-%d').date()

def format_date(d):
    return d.strftime('%Y-%m-%d')

def format_num(val):
    if val == int(val):
        return str(int(val))
    return f"{val:.2f}".rstrip('0').rstrip('.')

class DecisionEngine:
    def __init__(self, data_loader: DataLoader, simulator: CashFlowSimulator):
        self.dl = data_loader
        self.sim = simulator

    def evaluate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        req_id = request['request_id']
        uid = request['user_id']
        req_amt = float(request['requested_amount'])
        req_date_str = request['request_date']
        req_date = parse_date(req_date_str)
        desired_str = request.get('desired_completion_date', '')
        desired_date = parse_date(desired_str) if desired_str else req_date + timedelta(days=90)
        allows_partial = str(request.get('allows_partial_payment', '')).lower() in ('true', '1')

        profile = self.dl.profiles[uid]
        min_keep = profile['minimum_balance_to_keep']
        user_methods = profile['payment_methods_user_will_consider']
        max_install_months = profile['max_installment_months']

        # 1. Compute amount_safe_to_pay today (without spending changes)
        min_obs_bal, _ = self.sim.simulate(uid, req_date_str)
        headroom = min_obs_bal - min_keep
        amount_safe = max(0.0, min(headroom, req_amt))

        # 2. Compute earliest_date_for_full_payment
        earliest_full_date = ""
        if amount_safe >= req_amt:
            earliest_full_date = req_date_str
        else:
            for offset in range(91):
                cand_d = req_date + timedelta(days=offset)
                min_b, _ = self.sim.simulate(uid, req_date_str, extra_payments={cand_d: req_amt})
                if min_b >= min_keep:
                    earliest_full_date = format_date(cand_d)
                    break

        candidates = []

        # Candidate 1: Full Payment Today
        if 'full_payment' in user_methods and amount_safe >= req_amt:
            candidates.append({
                'status': 'affordable_now',
                'method': 'full_payment',
                'plan': f"{req_date_str}:{format_num(req_amt)}",
                'spending_changes': 'none',
                'completes_by_deadline': req_date <= desired_date,
                'no_spending_changes': True,
                'total_cost': req_amt,
                'start_date': req_date,
                'num_payments': 1,
                'option_id': 'opt_00'
            })

        # Candidate 2: Installments
        if 'installments' in user_methods:
            options = self.dl.payment_options_by_req.get(req_id, [])
            for opt in options:
                if opt['payment_method'] != 'installments':
                    continue
                num_pmts = opt['number_of_payments']
                freq = opt['payment_frequency_days'] or 30
                
                # Check max installment duration
                duration_days = (num_pmts - 1) * freq
                duration_months = round(duration_days / 30)
                if max_install_months is not None and duration_months > max_install_months:
                    continue

                first_d = parse_date(opt['first_payment_date'])
                pmts = {}
                cur = first_d
                for i in range(num_pmts):
                    pmts[cur] = opt['payment_amount']
                    cur += timedelta(days=freq)
                last_d = cur - timedelta(days=freq)

                # Check safety
                min_b, _ = self.sim.simulate(uid, req_date_str, extra_payments=pmts)
                if min_b >= min_keep:
                    plan_str = '|'.join(f"{format_date(d)}:{format_num(a)}" for d, a in sorted(pmts.items()))
                    candidates.append({
                        'status': 'affordable_with_plan',
                        'method': 'installments',
                        'plan': plan_str,
                        'spending_changes': 'none',
                        'completes_by_deadline': last_d <= desired_date,
                        'no_spending_changes': True,
                        'total_cost': opt['total_payable_amount'],
                        'start_date': first_d,
                        'num_payments': num_pmts,
                        'option_id': opt['payment_option_id']
                    })

        # Candidate 3: Partial Payment
        if allows_partial and 'partial_payment' in user_methods and 0 < amount_safe < req_amt:
            if earliest_full_date:
                earliest_d = parse_date(earliest_full_date)
                if earliest_d <= desired_date:
                    remainder = req_amt - amount_safe
                    pmts = {req_date: amount_safe, earliest_d: remainder}
                    min_b, _ = self.sim.simulate(uid, req_date_str, extra_payments=pmts)
                    if min_b >= min_keep:
                        plan_str = f"{req_date_str}:{format_num(amount_safe)}|{earliest_full_date}:{format_num(remainder)}"
                        candidates.append({
                            'status': 'affordable_with_plan',
                            'method': 'partial_payment',
                            'plan': plan_str,
                            'spending_changes': 'none',
                            'completes_by_deadline': earliest_d <= desired_date,
                            'no_spending_changes': True,
                            'total_cost': req_amt,
                            'start_date': req_date,
                            'num_payments': 2,
                            'option_id': 'partial'
                        })

        # Candidate 4: Spending Changes (if needed)
        if not candidates or not any(c['completes_by_deadline'] and c['no_spending_changes'] for c in candidates):
            # Try finding flexible spending changes
            stop_cats = profile['expense_categories_user_is_willing_to_stop']
            reduce_cats = profile['expense_categories_user_is_willing_to_reduce']
            recurring = self.sim.get_recurring_expenses(uid, req_date)
            
            cand_changes = []
            for r in recurring:
                cat = r['category']
                eid = r['event_id']
                flex = r['flexibility']
                if flex in ('stoppable', 'reducible_or_stoppable') and cat in stop_cats:
                    cand_changes.append(f"stop:{eid}")
                if flex in ('reducible', 'reducible_or_stoppable') and cat in reduce_cats and r['minimum_allowed_amount']:
                    cand_changes.append(f"reduce_to:{eid}:{format_num(r['minimum_allowed_amount'])}")

            # Test single and combinations up to 2 changes
            for ch in cand_changes:
                min_b, _ = self.sim.simulate(uid, req_date_str, extra_payments={req_date: req_amt}, spending_changes=[ch])
                if min_b >= min_keep and 'full_payment' in user_methods:
                    candidates.append({
                        'status': 'affordable_with_plan',
                        'method': 'full_payment',
                        'plan': f"{req_date_str}:{format_num(req_amt)}",
                        'spending_changes': ch,
                        'completes_by_deadline': req_date <= desired_date,
                        'no_spending_changes': False,
                        'total_cost': req_amt,
                        'start_date': req_date,
                        'num_payments': 1,
                        'option_id': 'spend_ch_1'
                    })
                    break

            if not candidates and len(cand_changes) >= 2:
                # Test pairs
                for i in range(len(cand_changes)):
                    for j in range(i + 1, len(cand_changes)):
                        ch_pair = [cand_changes[i], cand_changes[j]]
                        # Ensure not modifying the same event twice
                        e1 = cand_changes[i].split(':')[1]
                        e2 = cand_changes[j].split(':')[1]
                        if e1 == e2:
                            continue
                        min_b, _ = self.sim.simulate(uid, req_date_str, extra_payments={req_date: req_amt}, spending_changes=ch_pair)
                        if min_b >= min_keep and 'full_payment' in user_methods:
                            candidates.append({
                                'status': 'affordable_with_plan',
                                'method': 'full_payment',
                                'plan': f"{req_date_str}:{format_num(req_amt)}",
                                'spending_changes': '|'.join(ch_pair),
                                'completes_by_deadline': req_date <= desired_date,
                                'no_spending_changes': False,
                                'total_cost': req_amt,
                                'start_date': req_date,
                                'num_payments': 1,
                                'option_id': 'spend_ch_pair'
                            })
                            break
                    if candidates:
                        break

        # Select Best Candidate using 6-tier ranking
        best_cand = None
        if candidates:
            # Sort candidates by:
            # 1. completes_by_deadline (True first -> 0)
            # 2. no_spending_changes (True first -> 0)
            # 3. total_cost (lowest first)
            # 4. start_date (earliest first)
            # 5. num_payments (fewest first)
            # 6. option_id (alphabetical)
            candidates.sort(key=lambda c: (
                0 if c['completes_by_deadline'] else 1,
                0 if c['no_spending_changes'] else 1,
                c['total_cost'],
                c['start_date'],
                c['num_payments'],
                c['option_id']
            ))
            if candidates[0]['completes_by_deadline']:
                best_cand = candidates[0]

        # If no plan completes by deadline, check Wait
        if not best_cand:
            if earliest_full_date and 'full_payment' in user_methods:
                best_cand = {
                    'status': 'affordable_later',
                    'method': 'wait',
                    'plan': f"{earliest_full_date}:{format_num(req_amt)}",
                    'spending_changes': 'none'
                }
            else:
                best_cand = {
                    'status': 'not_affordable',
                    'method': 'not_recommended',
                    'plan': 'none',
                    'spending_changes': 'none'
                }

        # Build output row
        exp = generate_explanation(
            request=request,
            profile=profile,
            status=best_cand['status'],
            method=best_cand['method'],
            plan=best_cand['plan'],
            earliest_date=earliest_full_date,
            spending_changes=best_cand['spending_changes'],
            amount_safe=amount_safe,
            data_loader=self.dl
        )

        return {
            'request_id': req_id,
            'amount_safe_to_pay': round(amount_safe, 2),
            'affordability_status': best_cand['status'],
            'recommended_payment_method': best_cand['method'],
            'payment_plan': best_cand['plan'],
            'earliest_date_for_full_payment': earliest_full_date if best_cand['status'] != 'not_affordable' else '',
            'spending_changes_needed': best_cand['spending_changes'],
            'decision_explanation': exp
        }
