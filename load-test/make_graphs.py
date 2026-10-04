#!/usr/bin/env python3
"""
Graph Generation Script for Cloud Computing Lab Evaluation
Reads results/results.csv and produces 6 high-resolution publication-quality PNG charts
illustrating system performance metrics across concurrency tiers.
"""

import os
import csv
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend suitable for headless generation
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CSV_PATH = os.path.join(RESULTS_DIR, "results.csv")


def load_results():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Cannot find results file at {CSV_PATH}. Run load_test.py first.")

    rows = []
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "Workload": float(r["Workload"]),
                "Concurrency": int(float(r["Concurrency"])),
                "Response_Time_ms": float(r["Response_Time_ms"]),
                "Throughput_rps": float(r["Throughput_rps"]),
                "Failed": int(float(r["Failed"])),
                "Total_CPU_Percent": float(r["Total_CPU_Percent"]),
                "Total_Memory_MB": float(r["Total_Memory_MB"]),
                "Order_CPU": float(r["Order_CPU"]),
                "Order_Mem_MB": float(r["Order_Mem_MB"]),
                "Restaurant_CPU": float(r["Restaurant_CPU"]),
                "Restaurant_Mem_MB": float(r["Restaurant_Mem_MB"]),
                "Delivery_CPU": float(r["Delivery_CPU"]),
                "Delivery_Mem_MB": float(r["Delivery_Mem_MB"]),
            })
    return rows


def setup_plot_style():
    plt.rcParams.update({
        "font.sans-serif": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.labelweight": "semibold",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "figure.titleweight": "bold",
        "grid.color": "#e0e0e0",
        "grid.linestyle": "--",
        "grid.linewidth": 0.8,
        "grid.alpha": 0.7,
    })


def annotate_points(ax, x_vals, y_vals, offset=(0, 7), fmt="{:.1f}"):
    for x, y in zip(x_vals, y_vals):
        ax.annotate(fmt.format(y),
                    (x, y),
                    textcoords="offset points",
                    xytext=offset,
                    ha='center',
                    fontsize=8.5,
                    fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#cccccc", alpha=0.8))


def generate_all_graphs():
    data = load_results()
    setup_plot_style()

    concurrency = [r["Concurrency"] for r in data]
    resp_times = [r["Response_Time_ms"] for r in data]
    throughput = [r["Throughput_rps"] for r in data]
    total_cpu = [r["Total_CPU_Percent"] for r in data]
    total_mem = [r["Total_Memory_MB"] for r in data]

    order_cpu = [r["Order_CPU"] for r in data]
    rest_cpu = [r["Restaurant_CPU"] for r in data]
    deliv_cpu = [r["Delivery_CPU"] for r in data]

    order_mem = [r["Order_Mem_MB"] for r in data]
    rest_mem = [r["Restaurant_Mem_MB"] for r in data]
    deliv_mem = [r["Delivery_Mem_MB"] for r in data]

    # -------------------------------------------------------------
    # Graph 1: Concurrency vs Avg Response Time
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot(concurrency, resp_times, marker='o', color='#2563eb', linewidth=2.5, markersize=8, label="Avg Latency (ms)")
    annotate_points(ax, concurrency, resp_times, fmt="{:.1f} ms")
    ax.set_title("Graph 1: Concurrency vs. Average Response Time")
    ax.set_xlabel("Concurrency Level (Concurrent Clients)")
    ax.set_ylabel("Response Time (ms)")
    ax.set_xticks(concurrency)
    ax.grid(True)
    ax.legend(loc="upper left", frameon=True)
    fig.tight_layout()
    p1 = os.path.join(RESULTS_DIR, "graph1_response_time.png")
    fig.savefig(p1)
    plt.close(fig)
    print(f"[+] Saved {p1}")

    # -------------------------------------------------------------
    # Graph 2: Concurrency vs Throughput
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot(concurrency, throughput, marker='s', color='#16a34a', linewidth=2.5, markersize=8, label="Throughput (rps)")
    annotate_points(ax, concurrency, throughput, fmt="{:.1f} rps")
    ax.set_title("Graph 2: Concurrency vs. System Throughput")
    ax.set_xlabel("Concurrency Level (Concurrent Clients)")
    ax.set_ylabel("Throughput (Requests Per Second)")
    ax.set_xticks(concurrency)
    ax.grid(True)
    ax.legend(loc="lower right", frameon=True)
    fig.tight_layout()
    p2 = os.path.join(RESULTS_DIR, "graph2_throughput.png")
    fig.savefig(p2)
    plt.close(fig)
    print(f"[+] Saved {p2}")

    # -------------------------------------------------------------
    # Graph 3: Concurrency vs Total CPU Utilization %
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot(concurrency, total_cpu, marker='^', color='#dc2626', linewidth=2.5, markersize=8, label="Total System CPU (%)")
    annotate_points(ax, concurrency, total_cpu, fmt="{:.1f}%")
    ax.set_title("Graph 3: Concurrency vs. Total CPU Utilization (%)")
    ax.set_xlabel("Concurrency Level (Concurrent Clients)")
    ax.set_ylabel("Total CPU Utilization (%)")
    ax.set_xticks(concurrency)
    ax.grid(True)
    ax.legend(loc="upper left", frameon=True)
    fig.tight_layout()
    p3 = os.path.join(RESULTS_DIR, "graph3_cpu.png")
    fig.savefig(p3)
    plt.close(fig)
    print(f"[+] Saved {p3}")

    # -------------------------------------------------------------
    # Graph 4: Concurrency vs Total Memory Usage (MB)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot(concurrency, total_mem, marker='D', color='#9333ea', linewidth=2.5, markersize=8, label="Total System Memory (MB)")
    annotate_points(ax, concurrency, total_mem, fmt="{:.1f} MB")
    ax.set_title("Graph 4: Concurrency vs. Total Memory Usage (MB)")
    ax.set_xlabel("Concurrency Level (Concurrent Clients)")
    ax.set_ylabel("Total Memory (MB)")
    ax.set_xticks(concurrency)
    ax.grid(True)
    ax.legend(loc="lower right", frameon=True)
    fig.tight_layout()
    p4 = os.path.join(RESULTS_DIR, "graph4_memory.png")
    fig.savefig(p4)
    plt.close(fig)
    print(f"[+] Saved {p4}")

    # -------------------------------------------------------------
    # Graph 5: CPU % breakdown curves for all three services
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    ax.plot(concurrency, order_cpu, marker='o', color='#ea580c', linewidth=2.2, markersize=7, label="Order Service (Orchestrator)")
    ax.plot(concurrency, rest_cpu, marker='s', color='#0284c7', linewidth=2.2, markersize=7, label="Restaurant Service")
    ax.plot(concurrency, deliv_cpu, marker='^', color='#059669', linewidth=2.2, markersize=7, label="Delivery Service")
    ax.set_title("Graph 5: Service-Level CPU Utilization Breakdown")
    ax.set_xlabel("Concurrency Level (Concurrent Clients)")
    ax.set_ylabel("CPU Utilization (%)")
    ax.set_xticks(concurrency)
    ax.grid(True)
    ax.legend(loc="upper left", frameon=True)
    fig.tight_layout()
    p5 = os.path.join(RESULTS_DIR, "graph5_cpu_per_service.png")
    fig.savefig(p5)
    plt.close(fig)
    print(f"[+] Saved {p5}")

    # -------------------------------------------------------------
    # Graph 6: Memory MB breakdown curves for all three services
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    ax.plot(concurrency, order_mem, marker='o', color='#ea580c', linewidth=2.2, markersize=7, label="Order Service")
    ax.plot(concurrency, rest_mem, marker='s', color='#0284c7', linewidth=2.2, markersize=7, label="Restaurant Service")
    ax.plot(concurrency, deliv_mem, marker='^', color='#059669', linewidth=2.2, markersize=7, label="Delivery Service")
    ax.set_title("Graph 6: Service-Level Memory Consumption Breakdown")
    ax.set_xlabel("Concurrency Level (Concurrent Clients)")
    ax.set_ylabel("Memory Usage (MB)")
    ax.set_xticks(concurrency)
    ax.grid(True)
    ax.legend(loc="lower right", frameon=True)
    fig.tight_layout()
    p6 = os.path.join(RESULTS_DIR, "graph6_memory_per_service.png")
    fig.savefig(p6)
    plt.close(fig)
    print(f"[+] Saved {p6}")

    print("\n[+] All 6 graphs successfully generated in results/")


if __name__ == "__main__":
    generate_all_graphs()
