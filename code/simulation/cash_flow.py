import os
import sys
from datetime import date, datetime, timedelta
from collections import defaultdict, Counter
import re

sys.path.append('code')
from simulation.data_loader import DataLoader

def parse_date(d_str):
    if not d_str:
        return None
    if isinstance(d_str, date):
        return d_str
    try:
        return date(int(d_str[:4]), int(d_str[5:7]), int(d_str[8:10]))
    except Exception:
        return None

def format_date(d):
    return d.strftime('%Y-%m-%d')

class CashFlowSimulator:
    def __init__(self, data_loader: DataLoader):
        self.dl = data_loader
        self._salary_cache = {}
        self._recurring_cache = {}
        self._future_scheduled_cache = {}

    def get_salary_info(self, user_id, request_date):
        cache_key = (user_id, request_date)
        if cache_key in self._salary_cache:
            return self._salary_cache[cache_key]
        events = self.dl.events_by_user[user_id]
        
        # Check messages for salary overrides or terminations
        user_msgs = self.dl.messages_by_user.get(user_id, [])
        msg_salary_amt = None
        msg_salary_day = None
        no_future_salary = False
        
        for m in user_msgs:
            txt = m['message_text']
            if 'contract has ended' in txt or 'no further scheduled' in txt or 'final employer' in txt.lower():
                no_future_salary = True
            
            amt_match = re.search(r'(?:gaji|salary|pay).*?(?:IDR|EUR|USD|ZAR|INR)\s*([\d,]+(?:\.\d+)?)', txt, re.IGNORECASE)
            if not amt_match:
                amt_match = re.search(r'(?:IDR|EUR|USD|ZAR|INR)\s*([\d,]+(?:\.\d+)?)', txt)
            date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', txt)
            
            if amt_match:
                val_str = amt_match.group(1).replace(',', '')
                try:
                    msg_salary_amt = float(val_str)
                except ValueError:
                    pass
            if date_match:
                d = parse_date(date_match.group(1))
                msg_salary_day = d.day

        # Check if last salary was "Final"
        salaries = [e for e in events if e['category'] == 'salary']
        if salaries:
            salaries.sort(key=lambda x: x['settlement_date_parsed'] or x['event_date_parsed'] or date.min)
            last_sal = salaries[-1]
            if 'final' in last_sal['description'].lower() or ('temporary' in last_sal['description'].lower() and 'ended' in last_sal['description'].lower()):
                no_future_salary = True

        if no_future_salary:
            res = (0.0, None, None)
            self._salary_cache[cache_key] = res
            return res

        # Check confirmed scheduled salary event
        for e in events:
            if e['category'] == 'salary' and e['status'] in ('scheduled', 'pending'):
                s_date = e['settlement_date_parsed'] or e['event_date_parsed']
                if s_date and s_date >= request_date:
                    amt = msg_salary_amt if msg_salary_amt is not None else e['amount']
                    day = msg_salary_day if msg_salary_day is not None else s_date.day
                    res = (amt, day, s_date)
                    self._salary_cache[cache_key] = res
                    return res

        # Fallback to settled salaries (pick the most common payday, e.g. 15th)
        settled_salaries = [e for e in salaries if e['status'] == 'settled']
        if settled_salaries:
            days = [(s['settlement_date_parsed'] or s['event_date_parsed']).day for s in settled_salaries if (s['settlement_date_parsed'] or s['event_date_parsed'])]
            most_common_day = Counter(days).most_common(1)[0][0] if days else 15
            last_sal = settled_salaries[-1]
            amt = msg_salary_amt if msg_salary_amt is not None else last_sal['amount']
            day = msg_salary_day if msg_salary_day is not None else most_common_day
            res = (amt, day, last_sal)
            self._salary_cache[cache_key] = res
            return res

        res = (0.0, 15, None)
        self._salary_cache[cache_key] = res
        return res

    def get_recurring_expenses(self, user_id, request_date):
        cache_key = (user_id, request_date)
        if cache_key in self._recurring_cache:
            return self._recurring_cache[cache_key]

        events = self.dl.events_by_user[user_id]
        past_events = [e for e in events if (e['settlement_date_parsed'] or e['event_date_parsed']) and (e['settlement_date_parsed'] or e['event_date_parsed']) <= request_date]
        
        # Group by description
        by_desc = defaultdict(list)
        for e in past_events:
            if e['direction'] == 'debit' and e['status'] == 'settled':
                d = e['settlement_date_parsed'] or e['event_date_parsed']
                by_desc[e['description']].append((d, e))

        recurring = []
        for desc, occurrences in by_desc.items():
            occurrences.sort(key=lambda x: x[0])
            last_d, last_e = occurrences[-1]
            
            # An expense is recurring if it occurred at least 2 times, or if it occurred in the last 45 days
            if len(occurrences) >= 2 or (request_date - last_d).days <= 35:
                diffs = [(occurrences[i][0] - occurrences[i-1][0]).days for i in range(1, len(occurrences))] if len(occurrences) >= 2 else [30]
                avg_diff = sum(diffs) / len(diffs) if diffs else 30
                
                if 22 <= avg_diff <= 35:
                    recurring.append({
                        'type': 'monthly',
                        'day': last_d.day,
                        'last_date': last_d,
                        'amount': last_e['amount'],
                        'category': last_e['category'],
                        'description': desc,
                        'event_id': last_e['event_id'],
                        'flexibility': last_e['flexibility'],
                        'minimum_allowed_amount': last_e['minimum_allowed_amount']
                    })
                elif 5 <= avg_diff <= 18:
                    recurring.append({
                        'type': 'weekly',
                        'weekday': last_d.weekday(),
                        'interval_days': 7 if avg_diff <= 10 else 14,
                        'last_date': last_d,
                        'amount': last_e['amount'],
                        'category': last_e['category'],
                        'description': desc,
                        'event_id': last_e['event_id'],
                        'flexibility': last_e['flexibility'],
                        'minimum_allowed_amount': last_e['minimum_allowed_amount']
                    })
        self._recurring_cache[cache_key] = recurring
        return recurring

    def simulate(self, user_id, request_date_str, extra_payments=None, spending_changes=None, horizon_days=90):
        req_date = parse_date(request_date_str)
        p = self.dl.profiles[user_id]
        bal = p['current_available_balance'] - self.dl.pending_debits_by_user[user_id]
        
        # Account for explicitly scheduled future events in dataset (cached)
        fs_key = (user_id, req_date)
        if fs_key not in self._future_scheduled_cache:
            fs = defaultdict(float)
            events = self.dl.events_by_user[user_id]
            for e in events:
                if e['status'] == 'scheduled' and e['category'] != 'salary':
                    d = e['settlement_date_parsed'] or e['event_date_parsed']
                    if d and d >= req_date:
                        if e['direction'] == 'debit':
                            fs[d] += e['amount']
                        elif e['direction'] == 'credit':
                            fs[d] -= e['amount']
            self._future_scheduled_cache[fs_key] = fs
        future_scheduled = self._future_scheduled_cache[fs_key]

        salary_amt, salary_day, _ = self.get_salary_info(user_id, req_date)
        recurring_expenses = self.get_recurring_expenses(user_id, req_date)

        stop_eids = set()
        reduce_eids = {}
        if spending_changes:
            for ch in spending_changes:
                if ch.startswith('stop:'):
                    stop_eids.add(ch.split(':')[1])
                elif ch.startswith('reduce_to:'):
                    parts = ch.split(':')
                    reduce_eids[parts[1]] = float(parts[2])

        min_observed_bal = bal
        daily_balances = {}

        for offset in range(horizon_days + 1):
            cur_date = req_date + timedelta(days=offset)
            
            # Extra payments (from proposed plan)
            if extra_payments and cur_date in extra_payments:
                bal -= extra_payments[cur_date]

            # Future scheduled events in dataset
            if cur_date in future_scheduled:
                bal -= future_scheduled[cur_date]

            # Salary credit
            if salary_day is not None and cur_date.day == salary_day and cur_date > req_date:
                bal += salary_amt

            # Recurring expenses
            for rec in recurring_expenses:
                eid = rec['event_id']
                if eid in stop_eids:
                    continue
                amt = reduce_eids.get(eid, rec['amount'])

                if rec['type'] == 'monthly':
                    if cur_date > req_date and cur_date.day == rec['day']:
                        bal -= amt
                    elif cur_date == req_date and cur_date.day == rec['day'] and rec.get('last_date') and rec['last_date'] < req_date:
                        bal -= amt
                elif rec['type'] == 'weekly' and cur_date.weekday() == rec['weekday'] and cur_date > req_date:
                    days_since_last = (cur_date - rec['last_date']).days
                    if days_since_last > 0 and days_since_last % rec['interval_days'] == 0:
                        bal -= amt

            daily_balances[cur_date] = bal
            if bal < min_observed_bal:
                min_observed_bal = bal

        return min_observed_bal, daily_balances
