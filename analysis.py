"""
RavenStack SaaS Analytics — Multi-Table SQL Analysis
=======================================================
Real relational dataset: accounts, subscriptions, feature_usage,
support_tickets, churn_events. Analyzes churn drivers, feature
adoption, and support impact using JOINs and window functions.

Dataset source: RavenStack synthetic SaaS dataset by River @ Rivalytics
(https://rivalytics.medium.com) — used under MIT-like license, credited per terms.
"""

import sqlite3

conn = sqlite3.connect("ravenstack.db")
cur = conn.cursor()


def run(title, query):
    print("=" * 95)
    print(title)
    print("=" * 95)
    cur.execute(query)
    cols = [d[0] for d in cur.description]
    print(" | ".join(cols))
    print("-" * 95)
    for row in cur.fetchall():
        print(" | ".join(str(x) for x in row))
    print()


# ---------------------------------------------------------------
# Q1: Overall churn rate (accounts table)
# ---------------------------------------------------------------
run("Q1: Overall Account Churn Rate", """
SELECT
    COUNT(*) AS total_accounts,
    SUM(churn_flag) AS churned_accounts,
    ROUND(100.0 * SUM(churn_flag) / COUNT(*), 1) AS churn_rate_pct
FROM accounts;
""")

# ---------------------------------------------------------------
# Q2: Churn rate by plan tier and industry
# ---------------------------------------------------------------
run("Q2: Churn Rate by Plan Tier", """
SELECT
    plan_tier,
    COUNT(*) AS total_accounts,
    SUM(churn_flag) AS churned,
    ROUND(100.0 * SUM(churn_flag) / COUNT(*), 1) AS churn_rate_pct
FROM accounts
GROUP BY plan_tier
ORDER BY churn_rate_pct DESC;
""")

run("Q3: Churn Rate by Referral Source", """
SELECT
    referral_source,
    COUNT(*) AS total_accounts,
    SUM(churn_flag) AS churned,
    ROUND(100.0 * SUM(churn_flag) / COUNT(*), 1) AS churn_rate_pct
FROM accounts
GROUP BY referral_source
ORDER BY churn_rate_pct DESC;
""")

# ---------------------------------------------------------------
# Q4: JOIN — churn reason breakdown (churn_events + accounts)
# ---------------------------------------------------------------
run("Q4: Top Churn Reasons (JOIN accounts + churn_events)", """
SELECT
    ce.reason_code,
    COUNT(*) AS num_churns,
    ROUND(AVG(ce.refund_amount_usd), 2) AS avg_refund_usd,
    SUM(ce.preceding_downgrade_flag) AS had_downgrade_first
FROM churn_events ce
JOIN accounts a ON ce.account_id = a.account_id
GROUP BY ce.reason_code
ORDER BY num_churns DESC;
""")

# ---------------------------------------------------------------
# Q5: JOIN — does support ticket volume predict churn?
# (support_tickets + accounts)
# ---------------------------------------------------------------
run("Q5: Support Ticket Volume vs Churn (JOIN support_tickets + accounts)", """
SELECT
    ticket_bucket,
    COUNT(*) AS accounts_in_bucket,
    SUM(churned) AS churned_accounts,
    ROUND(100.0 * SUM(churned) / COUNT(*), 1) AS churn_rate_pct
FROM (
    SELECT
        a.account_id,
        a.churn_flag AS churned,
        COUNT(t.ticket_id) AS ticket_count,
        CASE
            WHEN COUNT(t.ticket_id) = 0 THEN '0 tickets'
            WHEN COUNT(t.ticket_id) <= 2 THEN '1-2 tickets'
            WHEN COUNT(t.ticket_id) <= 5 THEN '3-5 tickets'
            ELSE '6+ tickets'
        END AS ticket_bucket
    FROM accounts a
    LEFT JOIN support_tickets t ON a.account_id = t.account_id
    GROUP BY a.account_id
)
GROUP BY ticket_bucket
ORDER BY MIN(ticket_count);
""")

# ---------------------------------------------------------------
# Q6: JOIN — average satisfaction score by escalation status
# ---------------------------------------------------------------
run("Q6: Support Satisfaction Score by Escalation Status", """
SELECT
    escalation_flag,
    COUNT(*) AS total_tickets,
    ROUND(AVG(satisfaction_score), 2) AS avg_satisfaction,
    ROUND(AVG(resolution_time_hours), 1) AS avg_resolution_hours
FROM support_tickets
WHERE satisfaction_score IS NOT NULL
GROUP BY escalation_flag;
""")

# ---------------------------------------------------------------
# Q7: JOIN — feature usage depth vs subscription churn
# (feature_usage + subscriptions)
# ---------------------------------------------------------------
run("Q7: Feature Adoption Depth vs Subscription Churn (JOIN feature_usage + subscriptions)", """
SELECT
    usage_bucket,
    COUNT(*) AS subscriptions_in_bucket,
    SUM(churned) AS churned,
    ROUND(100.0 * SUM(churned) / COUNT(*), 1) AS churn_rate_pct
FROM (
    SELECT
        s.subscription_id,
        s.churn_flag AS churned,
        COUNT(DISTINCT fu.feature_name) AS distinct_features_used,
        CASE
            WHEN COUNT(DISTINCT fu.feature_name) <= 2 THEN '1-2 features'
            WHEN COUNT(DISTINCT fu.feature_name) <= 5 THEN '3-5 features'
            WHEN COUNT(DISTINCT fu.feature_name) <= 10 THEN '6-10 features'
            ELSE '11+ features'
        END AS usage_bucket
    FROM subscriptions s
    LEFT JOIN feature_usage fu ON s.subscription_id = fu.subscription_id
    GROUP BY s.subscription_id
)
GROUP BY usage_bucket
ORDER BY MIN(distinct_features_used);
""")

# ---------------------------------------------------------------
# Q8: MRR lost to churn, by plan tier (subscriptions table)
# Real revenue-impact query — a genuinely business-relevant metric.
# ---------------------------------------------------------------
run("Q8: Monthly Recurring Revenue Lost to Churn, by Plan Tier", """
SELECT
    plan_tier,
    COUNT(*) AS churned_subscriptions,
    ROUND(SUM(mrr_amount), 2) AS total_mrr_lost,
    ROUND(AVG(mrr_amount), 2) AS avg_mrr_per_churned_sub
FROM subscriptions
WHERE churn_flag = 1
GROUP BY plan_tier
ORDER BY total_mrr_lost DESC;
""")

# ---------------------------------------------------------------
# Q9 (Window Function): Rank accounts by seats within each industry
# ---------------------------------------------------------------
run("Q9: Top 3 Largest Accounts (by Seats) per Industry (Window Function - RANK)", """
SELECT industry, account_name, seats, seat_rank
FROM (
    SELECT
        industry,
        account_name,
        seats,
        RANK() OVER (PARTITION BY industry ORDER BY seats DESC) AS seat_rank
    FROM accounts
)
WHERE seat_rank <= 3
ORDER BY industry, seat_rank;
""")

# ---------------------------------------------------------------
# Q10 (Window Function): Running cumulative signups over time
# ---------------------------------------------------------------
run("Q10: Monthly Signups + Running Cumulative Total (Window Function)", """
SELECT
    strftime('%Y-%m', signup_date) AS signup_month,
    COUNT(*) AS new_signups,
    SUM(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', signup_date)) AS cumulative_signups
FROM accounts
GROUP BY signup_month
ORDER BY signup_month;
""")

conn.close()
