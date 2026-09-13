# Buy or Wait? — Personal Financial Decision Agent

Built by **Skyee** for the **HackerRank Orchestrate** hackathon (September 2026).

---

## What is this?

Most banking apps tell you how much money you have *right now*. But that number is often misleading.

If you have $2,000 in your account and want to buy a $600 phone, your balance says yes. But if your rent is $1,500 in three days and you want to keep a $500 emergency buffer, spending that $600 today leaves you in trouble.

**Buy or Wait?** solves this by simulating your bank balance day-by-day for the next 90 days. It looks at:
- Confirmed paydays and upcoming bills (rent, utilities, subscriptions).
- Pending charges that haven't settled yet.
- Your personal safety cushion (a minimum balance you never want to drop below).
- Available payment options (upfront, 3-month/6-month installments, split payments).

Then it gives you a clear answer:
1. **Pay in full today** — if your balance stays above your safety cushion the whole time.
2. **Use an installment plan** — if breaking the cost into smaller monthly chunks keeps your balance safe.
3. **Pay half now, half later** — if partial payment is allowed by the seller.
4. **Wait** — finds the exact future date your next salary arrives so you can buy it safely.
5. **Pass / Not recommended** — if none of the options protect your minimum cushion.

---

## Why simulation instead of an LLM?

We intentionally didn't ask an LLM to do the financial math.

Language models are great for conversation, but they hallucinate numbers, make arithmetic mistakes, and struggle with strict calendar math. For something as critical as personal finances, you want exact calculations.

The engine here is a deterministic daily cash ledger:
- Walks through every single day from Day 0 to Day 90.
- Deducts pending debits on Day 0 so money already committed isn't double-spent.
- Adds confirmed salary on regular paydays.
- Deducts recurring living expenses (groceries, rent, bills).
- Checks every payment option against the user's minimum balance floor.
- Ranks candidate plans by lowest total cost, fewest installments, and earliest safe completion.

It runs locally in ~12 seconds across all 275 requests with zero external API calls, zero latency, and zero math errors.

---

## Quick Start

Requires Python 3.10+ (uses standard library only; no extra pip packages needed).

### 1. Run all evaluation requests
Processes all 250 requests in `dataset/requests.csv` and outputs `output.csv`:
```bash
python code/main.py
```

### 2. Test a specific request interactively
Want to see how the engine makes a decision for a single user? Run:
```bash
# Someone who can comfortably pay upfront today:
python code/test_request.py request_01

# Someone who needs a 3-part installment plan:
python code/test_request.py request_30

# Someone who should wait for their next paycheck:
python code/test_request.py request_28
```

### 3. Check ground truth accuracy
Evaluates the engine against the 25 official sample requests:
```bash
python code/evaluation/main.py
```

### 4. Run a 360-day (full year) projection
See how an account balance trends across 12 full months:
```bash
python code/simulate_360_days.py request_30
```

---

## How the Code is Organized

```text
code/
├── simulation/
│   ├── data_loader.py       # Reads profiles, recurring events, exchange rates, and receipt images
│   ├── cash_flow.py         # Day-by-day cash flow ledger (supports 90 to 360 day horizons)
│   ├── decision_engine.py   # Ranks upfront vs. installments vs. partial vs. waiting
│   └── explanation.py       # Generates clear explanations for recommendations
├── evaluation/
│   ├── main.py              # Compares predictions against the 25 public sample requests
│   └── usage_report.md      # Token/cost summary (required for hackathon submission)
├── test_request.py          # Interactive CLI tool to inspect any single request
├── simulate_360_days.py     # 12-month balance trajectory simulator
├── simulate_all_275.py      # Runs all 275 requests and prints summary stats
└── main.py                  # Full batch runner that creates output.csv
```

---

## Dataset Overview

The `dataset/` folder contains:
- `requests.csv`: The 250 evaluation requests to predict.
- `sample_requests.csv`: 25 reference examples with completed target outputs.
- `financial_profiles.csv`: User base currencies, current balances, and minimum buffers.
- `financial_events.csv`: History of past transactions, recurring bills, and scheduled salaries.
- `request_payment_options.csv`: Payment terms offered by merchants for each purchase.
- `exchange_rates.csv`: Fixed historical currency conversion rates.
- `messages.csv` & `images.csv`: Contextual notes and receipt images for missing amounts.

*Note: The raw datasets and local run logs are kept locally and excluded from git via `.gitignore` to keep the repo clean.*

---

## Results on the Full Dataset

When running across all 275 requests:
- **34.9% Not Affordable (96 requests)**: The purchase or available loans would compromise the user's emergency cushion.
- **26.2% Full Payment (72 requests)**: Safe to pay 100% upfront today.
- **19.6% Wait (54 requests)**: Safe to buy after an upcoming confirmed payday.
- **17.1% Installments (47 requests)**: Safe using a structured 3 to 6-month payment plan.
- **2.2% Partial Payment (6 requests)**: Split into two payments (half now, half on payday).

All 275 requests are simulated in ~12 seconds.

---

## Author

- **GitHub**: [@Skyee-exe](https://github.com/Skyee-exe)
- **Contest**: HackerRank Orchestrate (September 2026)
