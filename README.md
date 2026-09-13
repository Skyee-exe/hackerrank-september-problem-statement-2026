# Buy or Wait? — AI Financial Decision Agent

> Built by **Skyee** for the **HackerRank Orchestrate** Hackathon (September 2026).  
> Solves the 90-day personal expense affordability challenge across 250 evaluation requests in **0.38 seconds** with zero external API calls and zero safety buffer breaches.

---

## 1. What This Project Does

Most banking applications give users a dangerous illusion of purchasing power by only displaying their current available balance.

If you have **$2,000** in your checking account and want to purchase an **$800** laptop:
- A naive balance check says **Yes** ($2,000 > $800).
- But if your rent of **$1,400** is due in 4 days, an electricity bill of **$150** is pending, and your emergency buffer floor is **$500**, spending that $800 today causes an overdraft of -$350 before your next paycheck arrives.

**Buy or Wait?** is an autonomous financial decision agent that reconstructs a user's multi-month financial reality and simulates their cash balance day-by-day across a **90-day forecast horizon**.

For every purchase or payment request, the system evaluates:
1. **Confirmed Income**: Paydays, salary amounts, contract end-dates, and frequency.
2. **Fixed Commitments & Living Expenses**: Rent, utilities, loan repayments, and grocery spending.
3. **Pending Transactions**: Money already committed but not yet settled on Day 0.
4. **Emergency Safety Cushion**: A strict minimum balance the user must never breach.
5. **Merchant Payment Terms**: Upfront payment, multi-month installment offers (BNPL), and split partial payments.
6. **Flexible Spending Levers**: Discretionary subscriptions and non-essential expenses the user is willing to reduce or pause.

### The 5 Decision Outcomes
For each request, the agent provides a definitive, personalized recommendation:
- `full_payment` (`affordable_now`): Safe to pay 100% upfront today without touching the emergency buffer.
- `installments` (`affordable_with_plan`): Upfront payment breaches the buffer, but an offered 3-month or 6-month installment plan keeps the balance safely above the floor.
- `partial_payment` (`affordable_with_plan`): Safe to pay an initial portion today, completing the remaining balance when salary arrives before the user's deadline.
- `wait` (`affordable_later`): Not safe today, but safe on a specific future date once confirmed income clears.
- `not_recommended` (`not_affordable`): Unaffordable across all payment structures without compromising essential safety reserves.

---

## 2. Tech Stack & Engineering Choices

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Language** | **Python 3.10+** | High readability, clean standard library, cross-platform portability. |
| **Dependencies** | **Zero External Dependencies** | Built 100% with standard library (`csv`, `datetime`, `collections`, `re`, `argparse`, `statistics`, `math`). No `pip install` required. |
| **Simulation Core** | **Deterministic Cash Ledger** | Replaced hallucinating LLM arithmetic with an exact daily cash flow ledger. |
| **Optimization** | **Monotonic Stack & Superposition** | Evaluates candidate payment plans in $O(1)$ and $O(N)$ using prefix/suffix minimum scans. |
| **Stress Engine** | **Binary Stackflow Optimizer** | Fast binary search kernel capable of running 1,000,000 parameter simulations in 1.6 seconds. |
| **Multimodal Handling** | **Deterministic Feature Mapping** | Extracts verified amounts from receipt images (e.g. `image_01.png` to `image_16.png`) to fill missing transaction fields. |

### Why Deterministic Simulation Instead of an LLM?
Large Language Models are excellent at conversational reasoning, but notoriously unreliable for exact calendar arithmetic:
- LLMs hallucinate numbers, miscalculate compounding fee schedules, and struggle with multi-month calendar date shifts.
- LLM API calls take 1,500 ms to 3,000 ms per request, cost money per token, and risk downtime.
- Our deterministic ledger runs locally in **sub-millisecond latency (0.98 ms/request)**, costs **$0.00**, exposes **zero private financial data**, and guarantees **0 buffer breaches**.

---

## 3. Architecture & How It Works

```text
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           INPUT DATASETS                               │
  │  financial_profiles.csv │ financial_events.csv │ exchange_rates.csv    │
  │  request_payment_options.csv │ messages.csv │ media/images/*.png       │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 1. INGESTION & DATA RECONSTRUCTION                     │
  │  • Fast integer date parsing (YYYY-MM-DD -> date in 40ns)              │
  │  • Multi-currency conversion via fixed dated exchange rates            │
  │  • Multimodal receipt extraction for blank transaction amounts         │
  │  • Deducts pending debits immediately from starting balance            │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 2. 90-DAY CASH LEDGER SIMULATION                       │
  │  • Simulates daily balance curve: Balance(t) for t in [0..90]          │
  │  • Identifies payday cycles, recurring living bills, and future events │
  │  • Computes prefix_min[t] and suffix_min[t] arrays in O(N)             │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 3. MULTI-CANDIDATE EVALUATION & RANKING                │
  │  • Candidate 1: Full Payment Upfront (evaluates amount_safe_to_pay)    │
  │  • Candidate 2: Seller Installments (linear superposition in O(N))     │
  │  • Candidate 3: Partial Payment (O(1) prefix/suffix minimum check)     │
  │  • Candidate 4: Spending Adjustments (stop/reduce flexible expenses)   │
  │  • Ranks by: Deadline -> No Spending Changes -> Total Cost ->          │
  │              Earliest Start -> Fewer Payments                          │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                         4. FINAL OUTPUT EXPORT                         │
  │  • Writes compliant output.csv for all 250 evaluation requests         │
  │  • Generates grounded plain-English decision explanations              │
  │  • Records computational metrics in evaluation/usage_report.md         │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Quick Start & CLI Usage

### Prerequisites
- Python 3.10 or higher.
- No external libraries needed.

```bash
# Clone the repository
git clone https://github.com/Skyee-exe/hackerrank-september-problem-statement-2026.git
cd hackerrank-september-problem-statement-2026
```

---

### Key Commands

#### 1. Run the Full Evaluation Pipeline (`main.py`)
Processes all 250 evaluation requests, writes `output.csv`, and generates `evaluation/usage_report.md`:
```bash
python code/main.py
```

#### 2. Benchmark Problem Statement Latency (`check_latency.py`)
Runs statistical latency profiling ($P_{50}, P_{90}, P_{95}, P_{99}$) across the official evaluation dataset:
```bash
python code/evaluation/check_latency.py
```

#### 3. Test Custom Scenarios Interactively (`test_custom.py`)
Run an interactive terminal wizard that asks for your numbers, draws a 90-day ASCII balance trajectory curve against your emergency cushion line, and runs resilience stress-tests:
```bash
# Interactive mode (prompts in terminal):
python code/test_custom.py

# Shorthand CLI mode: python code/test_custom.py <balance> <cushion> <purchase>
python code/test_custom.py 50000 15000 20000
```

#### 4. Run Binary Stackflow & 1-Million Parameter Stress Test (`test_binary_stackflow.py`)
Tests binary search convergence down to $+\$0.0000$ margin and runs a 1,000,000-scenario Monte Carlo stress test:
```bash
# Run both the convergence demo and the 1M parameter test:
python code/test_binary_stackflow.py

# Run only the 1,000,000 parameter stress benchmark:
python code/test_binary_stackflow.py --1m
```

#### 5. Inspect a Specific Request from the Dataset (`test_request.py`)
Inspect the full financial breakdown, profile preferences, and simulation trace for any single evaluation request:
```bash
# Test upfront affordability:
python code/test_request.py request_01

# Test an installment recommendation:
python code/test_request.py request_30

# Test a waiting recommendation:
python code/test_request.py request_28
```

#### 6. Compare Against Alternative Models (`benchmark_comparison.py`)
Compares our 90-day simulator against a Naive Balance Check and a 30-Day Budget model (demonstrates how naive checks cause 52 buffer crashes):
```bash
python code/evaluation/benchmark_comparison.py
```

#### 7. Run Full Year (360-Day) Annual Projections (`simulate_360_days.py`)
Projects account health across 12 consecutive months:
```bash
python code/simulate_360_days.py request_30
```

---

## 5. Performance Benchmarks

All benchmarks measured on a standard developer machine (single CPU core, Python 3.12):

| Benchmark | Scope | Execution Time | Latency / Unit |
| :--- | :--- | :---: | :---: |
| **End-to-End Evaluation (`main.py`)** | 250 requests + CSV export | **0.38 s** | **1.52 ms / request** |
| **Request Decision Engine** | 250 requests | **0.25 s** | **0.98 ms / request** |
| **Median Request Latency ($P_{50}$)** | Individual request | — | **0.50 ms / request** |
| **95th Percentile Latency ($P_{95}$)** | Worst 5% requests | — | **3.39 ms / request** |
| **Binary Stackflow Kernel** | 1,000,000 scenarios | **1.63 s** | **1.63 $\mu$s / sim** (613k sims/sec) |
| **All 275 Requests (`simulate_all_275.py`)** | Samples + Evaluation | **0.39 s** | **1.43 ms / request** |
| **External Model Calls** | Runtime APIs | **0** | **$0.00 / 0 tokens** |

---

## 6. Correctness & Compliance Verification

The submission has been independently audited using strict programmatic invariants:
- **Schema & Formatting**: Exactly 8 columns matching the required output contract in order.
- **Bounds Invariant**: `0 <= amount_safe_to_pay <= requested_amount` across 100% of rows.
- **Date Invariant**: `earliest_date_for_full_payment` equals `request_date` for `affordable_now` and is valid or blank.
- **Plan Format**: Chronological `YYYY-MM-DD:amount` syntax matching merchant terms.
- **Capital Protection Audit**: 0 safety buffer breaches across all 250 evaluation requests.

---

## 7. Codebase Structure

```text
.
├── README.md                              # Project documentation
├── evaluation/
│   └── usage_report.md                    # Official token and computational usage report
└── code/
    ├── main.py                            # Official evaluation entrypoint (produces output.csv)
    ├── test_custom.py                     # Interactive custom test wizard with ASCII charts
    ├── test_binary_stackflow.py           # 1M parameter stress test & zero-margin convergence CLI
    ├── test_request.py                    # Single-request inspection tool
    ├── simulate_all_275.py                # Batch simulator across all 275 requests
    ├── simulate_360_days.py               # 12-month annual cash flow trajectory simulator
    ├── evaluation/
    │   ├── check_latency.py               # Statistical latency and percentile benchmark tool
    │   ├── benchmark_comparison.py        # Comparative benchmark against naive models
    │   ├── real_life_scenarios.py         # Real-world human persona simulation mapping
    │   ├── main.py                        # Public sample accuracy evaluator
    │   └── usage_report.md                # Submission cost/token artifact
    └── simulation/
        ├── data_loader.py                 # Multi-CSV loader, fast date parser, image extractions
        ├── cash_flow.py                   # 90-day cash ledger with memoized event caches
        ├── decision_engine.py             # Superposition evaluation and 6-tier ranking policy
        ├── binary_stackflow.py            # Monotonic stack flow and binary search optimizer
        └── explanation.py                 # Grounded plain-English explanation synthesizer
```

---

## 8. Summary of Evaluation Results

Across all 275 requests in the dataset:
- **34.9% Not Affordable (96 requests)**: Purchase would compromise the user's minimum emergency cushion.
- **26.2% Full Payment (72 requests)**: Safe to pay upfront immediately.
- **19.6% Wait (54 requests)**: Safe to purchase after an upcoming confirmed salary deposit.
- **17.1% Installments (47 requests)**: Safe using a merchant installment structure.
- **2.2% Partial Payment (6 requests)**: Split into two payments (part today, remainder on payday).

---

## Author & Submission Details
- **Author**: [@Skyee-exe](https://github.com/Skyee-exe)
- **Repository**: [Skyee-exe/hackerrank-september-problem-statement-2026](https://github.com/Skyee-exe/hackerrank-september-problem-statement-2026)
- **Challenge**: HackerRank Orchestrate (September 2026) — *Buy or Wait?*