import os
import csv
from datetime import datetime
from collections import defaultdict

# Verified multimodal extractions from dataset/media/images/
IMAGE_AMOUNTS = {
    'event_253': 4365000.0,    # image_01 (Net Pay IDR 4,365,000)
    'event_1442': 100000.0,   # image_02 (Balance Due INR 1,00,000)
    'event_1545': 41272.0,    # image_03 (Net Amount INR 41,272)
    'event_1700': 2854.0,     # image_04 (Item Bill INR 2,854)
    'event_1786': 704.05,     # image_05 (Total INR 704.05)
    'event_3051': 1995.0,     # image_06 (Total INR 1,995)
    'event_3231': 8528.0,     # image_07 (Grand Total INR 8,528)
    'event_4535': 15339.0,    # image_08 (Total Received INR 15,339)
    'event_5170': 723.0,      # image_09 (Total Received INR 723)
    'event_6033': 79679.26,   # image_10 (Total INR 79,679.26)
    'event_6859': 3650.0,     # image_11 (Balance INR 3,650)
    'event_7307': 33.50,      # image_12 (Total USD 33.50)
    'event_7941': 2298.0,     # image_13 (Total paid INR 2,298)
    'event_9421': 4543.0,     # image_14 (TOTAL INR 4,543)
    'event_9806': 9968.0,     # image_15 (Grand Total INR 9,968)
    'event_10521': 393.22,    # image_16 (Total INR 393.22)
}


class DataLoader:
    def __init__(self, data_dir='dataset'):
        self.data_dir = data_dir
        self.exchange_rates = {}
        self.profiles = {}
        self.events_by_user = defaultdict(list)
        self.events_by_id = {}
        self.payment_options_by_req = defaultdict(list)
        self.messages_by_user = defaultdict(list)
        self.messages_by_req = defaultdict(list)
        self.load_all()

    def load_all(self):
        self._load_exchange_rates()
        self._load_profiles()
        self._load_payment_options()
        self._load_messages()
        self._load_events()

    def _load_exchange_rates(self):
        path = os.path.join(self.data_dir, 'exchange_rates.csv')
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                pair = (row['from_currency'], row['to_currency'], row['rate_date'])
                try:
                    self.exchange_rates[pair] = float(row['rate'])
                except (ValueError, KeyError):
                    pass

    def convert_currency(self, amount, from_curr, to_curr, date_str):
        if not from_curr or not to_curr or from_curr == to_curr or amount == 0:
            return amount
        pair = (from_curr, to_curr, date_str)
        if pair in self.exchange_rates:
            return amount * self.exchange_rates[pair]
        # fallback: search by currency pair regardless of exact date
        matching = [r for k, r in self.exchange_rates.items() if k[0] == from_curr and k[1] == to_curr]
        if matching:
            return amount * matching[-1]
        # inverse rate check
        inv_pair = (to_curr, from_curr, date_str)
        if inv_pair in self.exchange_rates and self.exchange_rates[inv_pair] > 0:
            return amount / self.exchange_rates[inv_pair]
        return amount

    def _load_profiles(self):
        path = os.path.join(self.data_dir, 'financial_profiles.csv')
        with open(path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                u = row['user_id']
                self.profiles[u] = {
                    'user_id': u,
                    'home_currency': row['home_currency'],
                    'current_available_balance': float(row['current_available_balance']),
                    'minimum_balance_to_keep': float(row['minimum_balance_to_keep']),
                    'financial_priorities': set(row['financial_priorities'].split('|')) if row['financial_priorities'] else set(),
                    'expense_categories_to_protect': set(row['expense_categories_to_protect'].split('|')) if row['expense_categories_to_protect'] else set(),
                    'expense_categories_user_is_willing_to_reduce': set(row['expense_categories_user_is_willing_to_reduce'].split('|')) if row['expense_categories_user_is_willing_to_reduce'] else set(),
                    'expense_categories_user_is_willing_to_stop': set(row['expense_categories_user_is_willing_to_stop'].split('|')) if row['expense_categories_user_is_willing_to_stop'] else set(),
                    'payment_methods_user_will_consider': set(row['payment_methods_user_will_consider'].split('|')) if row['payment_methods_user_will_consider'] else set(),
                    'max_installment_months': int(row['max_installment_months']) if row['max_installment_months'].strip() else None
                }

    def _load_payment_options(self):
        path = os.path.join(self.data_dir, 'request_payment_options.csv')
        with open(path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                req_id = row['request_id']
                try:
                    num_payments = int(row['number_of_payments'])
                except (ValueError, KeyError):
                    num_payments = 1
                try:
                    freq = int(row['payment_frequency_days']) if row['payment_frequency_days'] else 0
                except ValueError:
                    freq = 0
                try:
                    fee = float(row['financing_fee']) if row['financing_fee'] else 0.0
                except ValueError:
                    fee = 0.0
                try:
                    total_amt = float(row['total_payable_amount']) if row['total_payable_amount'] else 0.0
                except ValueError:
                    total_amt = 0.0
                try:
                    pmt_amt = float(row['payment_amount']) if row['payment_amount'] else 0.0
                except ValueError:
                    pmt_amt = 0.0

                self.payment_options_by_req[req_id].append({
                    'payment_option_id': row['payment_option_id'],
                    'request_id': req_id,
                    'payment_method': row['payment_method'],
                    'payment_amount': pmt_amt,
                    'number_of_payments': num_payments,
                    'first_payment_date': row['first_payment_date'],
                    'payment_frequency_days': freq,
                    'financing_fee': fee,
                    'total_payable_amount': total_amt
                })

    def _load_messages(self):
        path = os.path.join(self.data_dir, 'messages.csv')
        with open(path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                u = row['user_id']
                req_id = row['request_id']
                self.messages_by_user[u].append(row)
                if req_id:
                    self.messages_by_req[req_id].append(row)

    def _load_events(self):
        path = os.path.join(self.data_dir, 'financial_events.csv')
        with open(path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                eid = row['event_id']
                uid = row['user_id']
                # Fill missing amounts from image extraction if blank
                raw_amt = row['amount'].strip()
                if not raw_amt and eid in IMAGE_AMOUNTS:
                    amt = IMAGE_AMOUNTS[eid]
                elif raw_amt:
                    try:
                        amt = float(raw_amt)
                    except ValueError:
                        amt = 0.0
                else:
                    amt = 0.0

                # Convert currency to user's home currency if needed
                home_curr = self.profiles[uid]['home_currency'] if uid in self.profiles else row['currency']
                settle_date = row['settlement_date'] or row['event_date']
                converted_amt = self.convert_currency(amt, row['currency'], home_curr, settle_date)

                min_allowed = row['minimum_allowed_amount'].strip()
                min_allowed_amt = float(min_allowed) if min_allowed else None
                if min_allowed_amt is not None and row['currency'] != home_curr:
                    min_allowed_amt = self.convert_currency(min_allowed_amt, row['currency'], home_curr, settle_date)

                event_dict = {
                    'event_id': eid,
                    'user_id': uid,
                    'event_type': row['event_type'],
                    'description': row['description'],
                    'category': row['category'],
                    'direction': row['direction'],
                    'amount': converted_amt,
                    'raw_amount': amt,
                    'currency': home_curr,
                    'orig_currency': row['currency'],
                    'event_date': row['event_date'],
                    'settlement_date': settle_date,
                    'status': row['status'],
                    'linked_event_id': row['linked_event_id'],
                    'flexibility': row['flexibility'],
                    'minimum_allowed_amount': min_allowed_amt
                }
                self.events_by_user[uid].append(event_dict)
                self.events_by_id[eid] = event_dict
