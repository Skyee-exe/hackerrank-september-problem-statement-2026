# 💡 Buy or Wait? — AI Financial Decision Agent

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Challenge](https://img.shields.io/badge/HackerRank-Orchestrate%202026-00EA64.svg?logo=hackerrank&logoColor=black)](https://www.hackerrank.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Built with Care](https://img.shields.io/badge/Engine-Deterministic%20Simulation-orange.svg)](#)

> **"Can I afford this laptop today?"**  
> You check your banking app: you have $3,500. The laptop is $800. Easy yes, right?  
> **Not so fast.** Next Monday, your $2,500 rent is due. You also keep an emergency cushion of $1,000 for unexpected medical bills or car repairs. If you buy the laptop today, your balance crashes to $200 by Tuesday morning. You're trapped.

**Buy or Wait?** is an empathetic, AI-powered financial decision agent built for the **HackerRank Orchestrate 2026** hackathon. It looks beyond the surface balance, forward-simulating your real-world financial life up to **360 days** to give honest, grounded, and personalized financial advice.

---

## ✨ Why This Matters (The Human Philosophy)

Money isn't just numbers on a screen—it's peace of mind. Most budgeting apps tell you where your money went *last month*. This agent tells you **what will happen to your life if you swipe your card today**.

Our decision engine is built on four core financial principles:

1. 🛡️ **The Emergency Cushion is Sacred**:
   Everyone has a `minimum_balance_to_keep`. Our simulator rejects any purchase or payment plan that breaches this buffer on *any* day over the forecast horizon.
2. 🚫 **No Phantom Money**:
   Pending bonuses, lottery winnings, investment gains, or verbal promises do **not** buy groceries. We only count confirmed cash once it has officially settled.
3. ❤️ **Respect Everyday Life**:
   Groceries, utilities, medicines, and protected categories are untouchable. We only ever suggest trimming flexible expenses (like streaming subscriptions) if the user explicitly marked them as adjustable.
4. 🧠 **Avoid the Debt Trap**:
   Installments (BNPL) can be helpful, but they shouldn't become shackles. The engine always favors plans that minimize total interest/financing fees and clear the debt as early as safely possible.

---

## 🧭 How It Works Under the Hood

Instead of trusting a probabilistic language model to guess financial math (which often hallucinates dates and miscalculates sums), we built a **high-precision cash flow simulator**:

```
                       HOW THE AGENT THINKS
                       
    [1. User Context]             [2. 90-to-360 Day Simulation]         [3. Decision Policy]
┌─────────────────────────┐     ┌───────────────────────────────┐     ┌──────────────────────┐
│ • Bank Balance          │     │ • Day 0: Deduct pending debts │     │ 1. Upfront Payment?  │
│ • Minimum Safety Buffer │────▶│ • Track Paydays & confirmed   │────▶│ 2. Installments?     │
│ • Rent, Bills, Subs     │     │   salaries                    │     │ 3. Split (Partial)?  │
│ • Document Receipts     │     │ • Project living expenses     │     │ 4. Wait for payday?  │
│ • Payment Options (BNPL)│     │ • Enforce safety cushion      │     │ 5. Trim subscriptions│
└─────────────────────────┘     └───────────────────────────────┘     └──────────────────────┘
                                                                                 │
                                                                                 ▼
                                                                      [4. Grounded Output]
                                                                      • Safe amount today
                                                                      • Affordable status
                                                                      • Payment schedule
                                                                      • Plain-English reason
```

---

## 🛠️ Interactive Exploration (Try It Yourself!)

We built practical, interactive command-line utilities so you can test individual requests, run full benchmarks, or simulate a full year.

### 1. Inspect Any Single Request
Inspect a user's balance, safety cushion, available merchant options, and the agent's simulated verdict:
```powershell
# Test a request from the sample ground truth:
python code/test_request.py request_01

# Test an installment recommendation (3-month BNPL):
python code/test_request.py request_30

# Test any evaluation request:
python code/test_request.py request_26
```

### 2. Full 360-Day (12-Month) Cash Flow Simulator
See what happens to an account over an entire year of rent, paydays, and bills:
```powershell
python code/simulate_360_days.py request_30
```

### 3. Benchmark Accuracy Against Ground Truth
Run the automated validation suite against the 25 official sample requests:
```powershell
python code/evaluation/main.py
```

### 4. Simulate All 275 Requests
Simulate every single request across the entire dataset in ~12 seconds:
```powershell
python code/simulate_all_275.py
```

### 5. Generate Official Evaluation Output
Process all 250 evaluation requests and regenerate `output.csv`:
```powershell
python code/main.py
```

---

## 📊 Dataset Ecosystem

```text
dataset/
├── financial_profiles.csv       # Home currencies, available balance, safety cushions
├── financial_events.csv         # Historical & recurring events (rent, groceries, salary)
├── exchange_rates.csv           # Fixed historical currency conversions
├── requests.csv                 # 250 official evaluation requests
├── sample_requests.csv          # 25 public sample requests with completed answers
├── request_payment_options.csv  # Merchant payment plans (Full, 3-mo, 6-mo, 12-mo, 24-mo)
├── messages.csv                 # Bank alerts, bonus announcements, contract notices
├── images.csv & media/images/   # Receipts and statements with missing transaction values
└── output.csv                   # Target submission format
```

> **Data Privacy & Repo Cleanliness:**  
> Raw datasets, receipts, and execution audit logs are kept locally and excluded via `.gitignore` to keep this repository clean, lightweight, and professional.

---

## 📂 Codebase Architecture

```text
.
├── code/
│   ├── simulation/
│   │   ├── data_loader.py       # Data parser, dated exchange rates & image extraction
│   │   ├── cash_flow.py         # Configurable daily cash ledger simulator (90 to 360 days)
│   │   ├── decision_engine.py   # Multi-tier ranking policy & affordability engine
│   │   └── explanation.py       # Concise, human-grounded explanation generator
│   ├── evaluation/
│   │   ├── main.py              # Automated ground-truth benchmark suite
│   │   └── usage_report.md      # Token and computational efficiency report
│   ├── test_request.py          # Interactive CLI request inspector
│   ├── simulate_360_days.py     # 12-month trajectory analysis tool
│   ├── simulate_all_275.py      # Whole-dataset simulation & distribution analytics
│   └── main.py                  # Production batch runner
├── NOTION_GUIDE.md              # In-depth architectural & conceptual study guide
├── problem_statement.md         # Original HackerRank challenge specification
├── output.csv                   # Verified predictions (250 requests)
└── README.md                    # You are here!
```

---

## 📋 Evaluation Output Schema

The final `output.csv` conforms strictly to the 8-column competition specification:

| Field | Description | Example |
|---|---|---|
| `request_id` | Unique ID of the purchase request | `request_30` |
| `amount_safe_to_pay` | Maximum safe expenditure today | `775.20` |
| `affordability_status` | Status category | `affordable_with_plan` |
| `recommended_payment_method` | Selected payment method | `installments` |
| `payment_plan` | Chronological payment schedule | `2026-04-06:268.74\|2026-05-06:268.74...` |
| `earliest_date_for_full_payment`| First date safe for a 100% upfront lump sum | `2026-04-06` |
| `spending_changes_needed` | Targeted spending adjustments | `none` |
| `decision_explanation` | Empathetic, grounded rationale | *"Use 3 installments of USD 268.74, starting 6 April 2026..."* |

---

## 👤 Author & Acknowledgments

- **Author:** [Skyee-exe](https://github.com/Skyee-exe)
- **Challenge:** HackerRank Orchestrate (September 2026) — *Buy or Wait?*
- **Built with:** Python 3.12, clean modular code, zero external runtime API dependencies, and a deep focus on financial health.
