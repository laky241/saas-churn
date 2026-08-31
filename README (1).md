# RavenStack SaaS Churn & Adoption Analytics

A multi-table SQL + Python project analyzing why SaaS customers churn, using a real relational dataset spanning accounts, subscriptions, feature usage, support tickets, and churn events.

## The Problem

Acquiring a new SaaS customer is expensive. Losing existing ones quietly kills growth even when new signups look healthy. This project asks: **who is churning, why, and how much revenue is it costing?**

## The Dataset

**RavenStack** — a synthetic but realistically-structured, relational SaaS dataset (500 accounts, 5,000 subscriptions, 25,000 feature usage events, 2,000 support tickets, 600 churn events), created by **River @ Rivalytics** ([rivalytics.medium.com](https://rivalytics.medium.com)), used here under its permissive MIT-like license with credit to the original author, as required.

| Table | Rows | What it captures |
|---|---|---|
| `accounts` | 500 | Company info, plan tier, industry, referral source, churn flag |
| `subscriptions` | 5,000 | Billing history, MRR/ARR, upgrades/downgrades, churn |
| `feature_usage` | 25,000 | Individual feature usage events per subscription |
| `support_tickets` | 2,000 | Ticket priority, resolution time, satisfaction score |
| `churn_events` | 600 | Churn reason codes, refunds, reactivations |

Tables are properly linked via foreign keys (`account_id`, `subscription_id`), allowing real multi-table JOIN analysis rather than a single flat file.

## What I Did

1. **Wrote 10 SQL queries** (`analysis.py`) spanning single-table aggregation, multi-table JOINs across all 5 tables, and window functions (`RANK() OVER`, running cumulative totals).
2. **Built a Python pipeline** (`pipeline_report.py`) that runs core metrics and outputs a structured CSV report — simulating a recurring automated report against live data.
3. **Synthesized findings into revenue-tied, actionable recommendations** (below).

## Key Findings

| Finding | Detail |
|---|---|
| **Missing features is the #1 churn reason** | 114 of 600 churn events (19%) cite "features" as the reason — more than pricing (91) or competitors (92) |
| **Churn is evenly spread across plan tiers (~22%)** | But the *revenue impact* is wildly uneven — see below |
| **Enterprise churn costs the most by far** | $926K in lost MRR from Enterprise churn alone, vs. $180K (Pro) and $72K (Basic) — Enterprise churn is disproportionately expensive despite similar churn *rates* |
| **Low feature adoption correlates with higher churn** | Subscriptions using only 1-2 features churn at 11.6%, vs. 9.4% for those using 6-10 features |
| **Referral source affects retention** | Event-sourced accounts churn at 30.2%, vs. only 14.6% for partner-referred accounts — nearly double |

## Recommendations

1. **Prioritize feature-gap analysis for Enterprise accounts specifically** — since "features" is the top churn reason overall, and Enterprise churn carries by far the highest revenue cost ($926K), understanding *which* features Enterprise customers feel are missing should be the highest-leverage product research initiative.
2. **Build an adoption nudge for accounts using ≤2 features** — low feature adoption correlates with meaningfully higher churn; a guided onboarding checklist or in-app feature discovery prompt could close this gap.
3. **Re-evaluate event-based acquisition channel quality** — a 30.2% churn rate for event-sourced accounts (vs. 14.6% for partner referrals) suggests event-driven signups may be lower-intent; worth investigating whether this is a targeting problem or an onboarding mismatch for that channel.

## How to Run

```bash
pip install pandas
python3 analysis.py           # runs all 10 SQL analysis queries
python3 pipeline_report.py    # generates the automated CSV report
```

## Tech Used

SQL (SQLite) · Python · pandas · Multi-table JOINs · Window Functions (`RANK() OVER`, `PARTITION BY`, running totals)

## Credits

Dataset: **RavenStack Synthetic SaaS Dataset** by River @ Rivalytics ([blog](https://rivalytics.medium.com)), used under its MIT-like license.
Analysis, pipeline, and findings: Lakshay Kapoor.
