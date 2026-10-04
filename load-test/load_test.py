#!/usr/bin/env python3
"""
Workload Testing Script for Cloud Computing Lab Evaluation
Executes tiered concurrency load testing against the microservice food delivery system
and measures response time, throughput, and Docker container resource utilization.
"""

import os
import sys
import time
import csv
import json
import random
import re
import subprocess
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:5000/order")
HEALTH_CHECK_URL = os.environ.get("HEALTH_CHECK_URL", "http://localhost:5000/health")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CSV_PATH = os.path.join(RESULTS_DIR, "results.csv")

WORKLOAD_TIERS = [1, 2, 4, 8, 16]
REQUESTS_PER_TIER = 100
ITEMS_POOL = ["1", "2", "3", "pizza", "burger", "pasta"]
CUSTOMER_NAMES = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry"]


def parse_memory_mb(mem_str: str) -> float:
    """Parses Docker memory string (e.g., '45.2MiB / 7.669GiB' or '12.5MB') into megabytes (float)."""
    try:
        used_part = mem_str.split("/")[0].strip()
        match = re.search(r"([\d\.]+)\s*([a-zA-Z]+)", used_part)
        if not match:
            return 0.0
        val = float(match.group(1))
        unit = match.group(2).lower()

        if "gib" in unit or "gb" in unit:
            return round(val * 1024.0, 2)
        elif "mib" in unit or "mb" in unit:
            return round(val, 2)
        elif "kib" in unit or "kb" in unit:
            return round(val / 1024.0, 2)
        elif "b" in unit:
            return round(val / (1024.0 * 1024.0), 2)
        return round(val, 2)
    except Exception:
        return 0.0


def parse_cpu_perc(cpu_str: str) -> float:
    """Parses Docker CPU percentage string (e.g., '12.34%') into float."""
    try:
        clean = cpu_str.replace("%", "").strip()
        return round(float(clean), 2)
    except Exception:
        return 0.0


def get_live_container_stats():
    """
    Executes 'docker stats --no-stream --format {{.Name}},{{.CPUPerc}},{{.MemUsage}}'
    and returns parsed stats for order, restaurant, and delivery services.
    """
    cmd = ["docker", "stats", "--no-stream", "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}}"]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
        if result.returncode != 0:
            return None
        lines = result.stdout.strip().splitlines()
        stats = {
            "order": {"cpu": 0.0, "mem": 0.0},
            "restaurant": {"cpu": 0.0, "mem": 0.0},
            "delivery": {"cpu": 0.0, "mem": 0.0}
        }
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                name = parts[0].lower()
                cpu = parse_cpu_perc(parts[1])
                mem = parse_memory_mb(parts[2])
                if "order" in name:
                    stats["order"]["cpu"] = cpu
                    stats["order"]["mem"] = mem
                elif "restaurant" in name:
                    stats["restaurant"]["cpu"] = cpu
                    stats["restaurant"]["mem"] = mem
                elif "delivery" in name:
                    stats["delivery"]["cpu"] = cpu
                    stats["delivery"]["mem"] = mem
        return stats
    except Exception as e:
        return None


def send_single_order(session: requests.Session):
    """Sends a single POST request to the order orchestrator and records latency and status."""
    payload = {
        "customer_name": f"{random.choice(CUSTOMER_NAMES)}-{random.randint(100, 999)}",
        "item_id": random.choice(ITEMS_POOL)
    }
    start_time = time.perf_counter()
    try:
        response = session.post(ORDER_SERVICE_URL, json=payload, timeout=10)
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        success = (response.status_code == 201)
        return success, latency_ms
    except Exception:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return False, latency_ms


def sample_active_container_stats(concurrency: int, duration_target: float = 1.6):
    """
    Samples container resource usage while sustaining active load at the specified concurrency
    so Docker stats captures the active processing profile accurately.
    """
    stop_event = threading.Event()

    def load_worker():
        s = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=2)
        s.mount("http://", adapter)
        while not stop_event.is_set():
            try:
                payload = {
                    "customer_name": f"Sampler-{random.choice(CUSTOMER_NAMES)}",
                    "item_id": random.choice(ITEMS_POOL)
                }
                s.post(ORDER_SERVICE_URL, json=payload, timeout=5)
            except Exception:
                pass

    with ThreadPoolExecutor(max_workers=concurrency + 1) as pool:
        for _ in range(concurrency):
            pool.submit(load_worker)
        # Allow load to establish across the network
        time.sleep(0.4)
        stats = get_live_container_stats()
        stop_event.set()

    return stats


def wait_for_services(max_attempts=30, delay=1.0):
    """Verifies that the services are online and responding before beginning load test."""
    print("[*] Checking order-service health at", HEALTH_CHECK_URL)
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.get(HEALTH_CHECK_URL, timeout=3)
            if r.status_code == 200:
                print(f"[+] order-service is ready! (attempt {attempt})")
                return True
        except Exception:
            pass
        print(f"    Waiting for services to become available... ({attempt}/{max_attempts})")
        time.sleep(delay)
    print("[-] Error: order-service did not respond in time.")
    return False


def run_benchmark():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if not wait_for_services():
        print("[-] Exiting: Services are not responding.")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(" STARTING CLOUD COMPUTING LAB EVALUATION WORKLOAD TEST")
    print(f" Target Endpoint : {ORDER_SERVICE_URL}")
    print(f" Workload Tiers  : Concurrency levels {WORKLOAD_TIERS}")
    print(f" Requests/Tier   : {REQUESTS_PER_TIER}")
    print("=" * 80 + "\n")

    results_data = []

    for concurrency in WORKLOAD_TIERS:
        print(f"[*] Running Tier: Concurrency = {concurrency} | Workload = {REQUESTS_PER_TIER} requests")

        latencies = []
        failed_count = 0
        tier_start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            adapter = requests.adapters.HTTPAdapter(pool_connections=concurrency, pool_maxsize=concurrency * 2)
            session = requests.Session()
            session.mount("http://", adapter)

            futures = [executor.submit(send_single_order, session) for _ in range(REQUESTS_PER_TIER)]
            for fut in as_completed(futures):
                success, lat = fut.result()
                latencies.append(lat)
                if not success:
                    failed_count += 1

        tier_duration = time.perf_counter() - tier_start

        # Measure active container CPU and Memory under this concurrency level
        stats = sample_active_container_stats(concurrency)
        if not stats:
            stats = get_live_container_stats() or {
                "order": {"cpu": 0.0, "mem": 0.0},
                "restaurant": {"cpu": 0.0, "mem": 0.0},
                "delivery": {"cpu": 0.0, "mem": 0.0}
            }

        order_cpu = stats["order"]["cpu"]
        order_mem = stats["order"]["mem"]
        rest_cpu = stats["restaurant"]["cpu"]
        rest_mem = stats["restaurant"]["mem"]
        deliv_cpu = stats["delivery"]["cpu"]
        deliv_mem = stats["delivery"]["mem"]

        total_cpu = round(order_cpu + rest_cpu + deliv_cpu, 2)
        total_mem = round(order_mem + rest_mem + deliv_mem, 2)

        # Aggregate latency & throughput
        avg_resp_time_ms = round(statistics.mean(latencies), 2) if latencies else 0.0
        p95_resp_time_ms = round(statistics.quantiles(latencies, n=20)[18], 2) if len(latencies) >= 20 else avg_resp_time_ms
        throughput_rps = round(REQUESTS_PER_TIER / tier_duration, 2) if tier_duration > 0 else 0.0

        print(f"    Duration         : {tier_duration:.2f} s")
        print(f"    Avg Latency      : {avg_resp_time_ms} ms (P95: {p95_resp_time_ms} ms)")
        print(f"    Throughput       : {throughput_rps} rps")
        print(f"    Failed Requests  : {failed_count}/{REQUESTS_PER_TIER}")
        print(f"    CPU (Total)      : {total_cpu}% [Order: {order_cpu}%, Rest: {rest_cpu}%, Deliv: {deliv_cpu}%]")
        print(f"    Mem (Total)      : {total_mem} MB [Order: {order_mem}MB, Rest: {rest_mem}MB, Deliv: {deliv_mem}MB]")
        print("-" * 80)

        tier_record = {
            "Workload": REQUESTS_PER_TIER,
            "Concurrency": concurrency,
            "Response_Time_ms": avg_resp_time_ms,
            "Throughput_rps": throughput_rps,
            "Failed": failed_count,
            "Total_CPU_Percent": total_cpu,
            "Total_Memory_MB": total_mem,
            "Order_CPU": order_cpu,
            "Order_Mem_MB": order_mem,
            "Restaurant_CPU": rest_cpu,
            "Restaurant_Mem_MB": rest_mem,
            "Delivery_CPU": deliv_cpu,
            "Delivery_Mem_MB": deliv_mem
        }
        results_data.append(tier_record)
        time.sleep(1.0)  # Brief pause between tiers for resource settling

    # Write to CSV
    fieldnames = [
        "Workload", "Concurrency", "Response_Time_ms", "Throughput_rps",
        "Failed", "Total_CPU_Percent", "Total_Memory_MB",
        "Order_CPU", "Order_Mem_MB",
        "Restaurant_CPU", "Restaurant_Mem_MB",
        "Delivery_CPU", "Delivery_Mem_MB"
    ]

    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results_data:
            writer.writerow(row)

    print(f"\n[+] Successfully saved benchmark results to {CSV_PATH}")
    return results_data


if __name__ == "__main__":
    run_benchmark()
