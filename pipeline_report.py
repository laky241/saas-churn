"""
RavenStack — Automated Daily Adoption & Churn Report Pipeline
================================================================
Ingests the RavenStack relational dataset and outputs a structured
report — designed to simulate a recurring (daily) automated pipeline
against live production data.
"""

import sqlite3
import csv
from datetime import datetime

DB_PATH = "ravenstack.db"
REPORT_PATH = "daily_adoption_report.csv"


def generate_report():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    run_date = datetime.now().strftime("%Y-%m-%d")
    report_rows = []

    # Overall churn rate
    cur.execute("SELECT ROUND(100.0 * SUM(churn_flag) / COUNT(*), 1) FROM accounts;")
    report_rows.append(["overall_churn_rate_pct", cur.fetchone()[0], run_date])

    # Churn rate by plan tier
    cur.execute("""
        SELECT plan_tier, ROUND(100.0 * SUM(churn_flag) / COUNT(*), 1)
        FROM accounts GROUP BY plan_tier;
    """)
    for tier, rate in cur.fetchall():
        report_rows.append([f"churn_rate_{tier.lower()}", rate, run_date])

    # Top churn reason
    cur.execute("""
        SELECT reason_code, COUNT(*) FROM churn_events
        GROUP BY reason_code ORDER BY COUNT(*) DESC LIMIT 1;
    """)
    top_reason, count = cur.fetchone()
    report_rows.append(["top_churn_reason", top_reason, run_date])
    report_rows.append(["top_churn_reason_count", count, run_date])

    # Total MRR lost to churn
    cur.execute("SELECT ROUND(SUM(mrr_amount), 2) FROM subscriptions WHERE churn_flag = 1;")
    report_rows.append(["total_mrr_lost_usd", cur.fetchone()[0], run_date])

    # Avg support satisfaction score
    cur.execute("SELECT ROUND(AVG(satisfaction_score), 2) FROM support_tickets WHERE satisfaction_score IS NOT NULL;")
    report_rows.append(["avg_support_satisfaction_score", cur.fetchone()[0], run_date])

    # Low feature adoption churn rate (1-2 features used)
    cur.execute("""
        SELECT ROUND(100.0 * SUM(churned) / COUNT(*), 1)
        FROM (
            SELECT s.subscription_id, s.churn_flag AS churned,
                   COUNT(DISTINCT fu.feature_name) AS features_used
            FROM subscriptions s
            LEFT JOIN feature_usage fu ON s.subscription_id = fu.subscription_id
            GROUP BY s.subscription_id
            HAVING features_used <= 2
        );
    """)
    report_rows.append(["low_feature_adoption_churn_rate_pct", cur.fetchone()[0], run_date])

    conn.close()

    with open(REPORT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value", "report_date"])
        writer.writerows(report_rows)

    print(f"Report generated: {REPORT_PATH}")
    print(f"Run date: {run_date}\n")
    print("Summary of key metrics:")
    print("-" * 55)
    for metric, value, _ in report_rows:
        print(f"  {metric:42s} {value}")


if __name__ == "__main__":
    generate_report()
