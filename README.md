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
| `schema.sql` | Tables, keys and `CHECK` constraints |
| `roles.sql` | Least-privilege database role for the app |
| `seed.sql` | Test data: one company, two services, two example customers |
| `.env.example` | Template for secrets — copy to `.env`, which is git-ignored |
| [`docs/er-model.md`](docs/er-model.md) | ER diagram of the database |
| [`docs/threat-model.md`](docs/threat-model.md) | Threat model and list of implemented security measures |

## Setup
Requires PostgreSQL.
```bash
createdb offer_copilot
psql -d offer_copilot -f schema.sql
psql -d offer_copilot -f roles.sql
psql -d offer_copilot -f seed.sql
cp .env.example .env    # then fill in real values
```

## Security
See [`docs/threat-model.md`](docs/threat-model.md): system overview, assets, entry points,
threats and mitigations, open risks, and the table of implemented security measures.

## Status
Work in progress: database schema, seed data, least-privilege role and threat model done.
Next: web app with login and access control, then LLM extraction with structured output (Pydantic).
