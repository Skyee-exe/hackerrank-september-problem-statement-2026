"""
Latency Profiler & Benchmark for the Problem Statement Dataset
==============================================================
Benchmarks the exact latency of solving the official HackerRank Orchestrate
"Buy or Wait?" problem statement across all 250 evaluation requests in dataset/requests.csv.
"""

import os
import sys
import time
import csv
import statistics

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

code_dir = os.path.abspath('code')
if code_dir not in sys.path:
    sys.path.append(code_dir)

from simulation.data_loader import DataLoader
from simulation.cash_flow import CashFlowSimulator
from simulation.decision_engine import DecisionEngine

def benchmark_latency(data_dir='dataset'):
    print("\n" + "="*76)
    print(" [*] BENCHMARKING ORIGINAL PROBLEM STATEMENT LATENCY (dataset/requests.csv)")
    print("="*76)

    # 1. Measure DataLoader Ingestion
    t0 = time.perf_counter()
    dl = DataLoader(data_dir=data_dir)
    t1 = time.perf_counter()
    loader_time = (t1 - t0) * 1000

    # 2. Measure Simulator Init
    t0 = time.perf_counter()
    sim = CashFlowSimulator(dl)
    engine = DecisionEngine(dl, sim)
    t1 = time.perf_counter()
    init_time = (t1 - t0) * 1000

    # 3. Load 250 evaluation requests
    req_path = os.path.join(data_dir, 'requests.csv')
    with open(req_path, 'r', encoding='utf-8') as f:
        requests = list(csv.DictReader(f))

    # 4. Measure Per-Request Latency
    per_request_latencies = []
    t_start_all = time.perf_counter()

    for req in requests:
        t_req_start = time.perf_counter()
        engine.evaluate_request(req)
        t_req_end = time.perf_counter()
        per_request_latencies.append((t_req_end - t_req_start) * 1000)

    t_end_all = time.perf_counter()
    total_eval_time = (t_end_all - t_start_all) * 1000
    total_pipeline_time = loader_time + init_time + total_eval_time

    # Compute Statistics
    per_request_latencies.sort()
    n = len(per_request_latencies)
    mean_lat = statistics.mean(per_request_latencies)
    median_lat = statistics.median(per_request_latencies)
    min_lat = min(per_request_latencies)
    max_lat = max(per_request_latencies)
    p90_lat = per_request_latencies[int(n * 0.90)]
    p95_lat = per_request_latencies[int(n * 0.95)]
    p99_lat = per_request_latencies[int(n * 0.99)]

    print(f"  Dataset Scope:       250 evaluation requests ({len(dl.events_by_id):,} historical financial events)")
    print(f"  User Profiles:       {len(dl.profiles):,} active user accounts")
    print("-" * 76)
    print(" [*] COMPONENT LATENCY BREAKDOWN:")
    print(f"  1. Data Ingestion & Pre-computation: {loader_time:8.2f} ms")
    print(f"  2. Simulator & Engine Init:          {init_time:8.2f} ms")
    print(f"  3. 250 Request Evaluations:          {total_eval_time:8.2f} ms  ({total_eval_time/1000:.3f} seconds)")
    print(f"  ------------------------------------------------")
    print(f"  TOTAL END-TO-END LATENCY:            {total_pipeline_time:8.2f} ms  ({total_pipeline_time/1000:.3f} seconds)")
    print("-" * 76)
    print(" [*] REQUEST-LEVEL LATENCY DISTRIBUTION (N = 250):")
    print(f"  * Fastest Request (Min):             {min_lat:8.3f} ms")
    print(f"  * Median Latency (P50):              {median_lat:8.3f} ms")
    print(f"  * Mean Latency:                      {mean_lat:8.3f} ms")
    print(f"  * 90th Percentile (P90):             {p90_lat:8.3f} ms")
    print(f"  * 95th Percentile (P95):             {p95_lat:8.3f} ms")
    print(f"  * 99th Percentile (P99):             {p99_lat:8.3f} ms")
    print(f"  * Worst-Case Request (Max):          {max_lat:8.3f} ms")
    print("=" * 76)
    print(" [i] SUMMARY:")
    print(f"  Average throughput: {n / (total_eval_time / 1000):,.1f} requests/second.")
    print("  Official usage report: check evaluation/usage_report.md")
    print("=" * 76 + "\n")

if __name__ == '__main__':
    benchmark_latency()
