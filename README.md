# Offer Copilot

Turns discovery-call notes into a ready-to-send offer draft.

## Problem
Small businesses spend hours writing offers after every sales call.
In a discovery call, a decision-maker named offer creation as one of
their biggest time sinks.

## Solution
1. Paste the notes from a discovery call.
2. An LLM extracts the customer's needs and picks matching services.
3. The offer is calculated from the database and exported as a draft.

## Core idea
The LLM extracts and selects. It never calculates prices.
Services and prices live in a relational database, totals are computed
in SQL. No hallucinated prices, every number is traceable.

## Why PostgreSQL?

Offer Copilot manages customers, services, offers and offer items. That is data with a fixed structure and clear relationships, including a many-to-many relationship between offers and services. The expected volume is small: around 100 customers with roughly 50 offers each, about 5,000 offers over the agency's lifetime. Consistency is critical, because a wrong price in an offer could cause real financial damage. So I rely on keys, constraints and transactions: an offer and its items are saved together or not at all. The workload is read-heavy (browsing services, viewing offers) with occasional writes. The only unstructured data are the discovery notes, which fit well into a TEXT column. The schema is expected to be stable. A relational database fits all of this, and PostgreSQL is free, mature, and scales far beyond our needs.

## Repository structure
| File | Content |
|---|---|
| `schema.sql` | Tables, keys, `CHECK` constraints and indexes |
| `roles.sql` | Least-privilege database role for the app |
| `seed.sql` | Hand-written test data: one company, eight services, two example customers, one test user |
| `seed_generated.sql` | Generated test data (AI-assisted script): 48 more customers, 500 offers, ~1,460 items |
| `db.py` | Data layer: all SQL queries, parameterized; offers saved in one transaction |
| `models.py` | Data models (`Service`, `Candidate`, `Customer`, `OfferSummary`, `OfferItem`) |
| `knapsack.py` | Optimizer: best combination of services within the budget (SE_14) |
| `main.py` | Command-line app: one command per use case (see Run) |
| `requirements.txt` | Python dependencies (pinned) |
| `.env.example` | Template for secrets — copy to `.env`, which is git-ignored |
| [`docs/database.md`](docs/database.md) | Use cases, design decisions, consistency, transactions, data |
| [`docs/er-model.md`](docs/er-model.md) | ER diagram with cardinalities, keys and indexes |
| [`docs/threat-model.md`](docs/threat-model.md) | Threat model and list of implemented security measures |

## Setup
Requires PostgreSQL and Python 3.12+.
```bash
# 1. Database
createdb offer_copilot
psql -d offer_copilot -f schema.sql
psql -d offer_copilot -f roles.sql
psql -d offer_copilot -f seed.sql
psql -d offer_copilot -f seed_generated.sql   # optional: realistic data volume

# 2. Python environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Connection settings (DATABASE_URL), then fill in real values
cp .env.example .env
```

## Run
```bash
export $(grep -v '^#' .env | xargs)
.venv/bin/python main.py services                      # services and prices
.venv/bin/python main.py customers                     # customers
.venv/bin/python main.py add-note 1 2026-11-20 "Wants an AI setup and a workshop"
.venv/bin/python main.py create-offer 1 --budget 5000 \
    --want "AI setup=10" --want "Workshop=5" --want "Custom integration=8"
.venv/bin/python main.py offers 1                      # offers of customer 1 with totals
.venv/bin/python main.py show-offer 1                  # items of offer 1
.venv/bin/python main.py set-status 1 sent
```
`create-offer` chooses the best combination of the wanted services within the budget
(knapsack, `--want "Service=priority"`), saves the offer with all items in one transaction
and prints the total calculated in SQL. All use cases: [`docs/database.md`](docs/database.md).

## Ownership
Solo project by Josef Rabl. AI assistance (Claude) is disclosed at the top of each document and file
where it was used. The knapsack algorithms in `knapsack.py` are written by me without AI.

## Security
See [`docs/threat-model.md`](docs/threat-model.md): system overview, assets, entry points,
threats and mitigations, open risks, and the table of implemented security measures.

## Status
Work in progress. Done: database schema with indexes, data layer with transactions, demo of the
main use case, least-privilege role, threat model. Next: web app with login and access control,
then LLM extraction with structured output (Pydantic).
