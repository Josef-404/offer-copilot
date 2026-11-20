# Database Design — Offer Copilot

> Drafted with AI assistance (Claude) from my schema, my design decisions in the README and my code;
> reviewed by me. The data layer (`db.py`) was written with AI assistance and tested by me.

## Use cases

The app is a command-line application (`main.py`); every SQL query lives in the data layer `db.py`.

| # | Use case | Command | Data layer | Status |
|---|---|---|---|---|
| 1 | List the services and current prices of the company | `services` | `load_services` | implemented |
| 2 | List the customers of the company | `customers` | `load_customers` | implemented |
| 3 | Store the discovery notes of a sales call | `add-note` | `add_discovery_note` | implemented |
| 4 | Build the best offer within the customer's budget and save it with all items in one transaction, recording who created it | `create-offer` | `load_services`, `save_offer`, `find_user_id` + `knapsack.py` | implemented |
| 5 | List all offers of a customer with status, creator and total (JOIN + GROUP BY) | `offers` | `list_offers` | implemented |
| 6 | Show the items of an offer and its total calculated in SQL | `show-offer` | `load_offer_items`, `offer_total` | implemented |
| 7 | Change the status of an offer (draft → sent → accepted / rejected) | `set-status` | `set_offer_status` | implemented |
| 8 | Log in, with roles and tenant isolation | — | — | not implemented yet (data model exists) |
| 9 | Manage customers and services through a web UI | — | — | not implemented yet |
| 10 | Extract the customer's needs from discovery notes with an LLM | — | — | not implemented yet |

Example run: see the README ("Run").

## Design decisions
- **Relational database (PostgreSQL)**: fixed structure, clear relationships, consistency matters
  more than flexibility. Full reasoning in the README ("Why PostgreSQL?").
- **n:m between offers and services** via the junction table `offer_items`. An offer contains many
  services, a service appears in many offers.
- **Price snapshot**: `offer_items.unit_price` copies the price at the moment of the offer. If a price
  in `services` changes later, offers that were already sent stay correct.
- **Prices are never calculated by the LLM.** Totals come from SQL (`SUM(quantity * unit_price)`),
  so every number in an offer is traceable.
- **Tenants**: `customers`, `services` and `users` belong to a `company`, so every query can be
  filtered by the company of the logged-in user.

ER diagram, cardinalities, keys and indexes: [`er-model.md`](er-model.md).

## Consistency
The database itself rejects invalid data, independent of the application code:

| Rule | Example |
|---|---|
| Primary keys | every table has `id SERIAL PRIMARY KEY` |
| Foreign keys | an offer item cannot point to a service that does not exist |
| `NOT NULL` | an offer always has a customer and a creator |
| `CHECK` | `quantity > 0`, `unit_price >= 0`, `status` only `draft` / `sent` / `accepted` / `rejected`, `role` only `admin` / `editor` / `viewer` |
| `UNIQUE` | one account per email |

## Transactions
`db.save_offer` writes the offer and all its items inside **one transaction**
(`with connection.transaction():`). If inserting any item fails (e.g. a service id that does
not exist), PostgreSQL rolls back the whole offer. There is never an offer without items or an
item without an offer (**atomicity**, the A in ACID).

PostgreSQL's default isolation level **Read Committed** is enough here: two users creating offers
at the same time write different rows and do not conflict.

## Indexing
PostgreSQL indexes primary keys and `UNIQUE` columns automatically, but not foreign keys. The
schema adds indexes on the foreign keys the app filters and joins by (`services.company_id`,
`offers.customer_id`, `offer_items.offer_id`, `discovery_notes.customer_id`). Details in
[`er-model.md`](er-model.md#indexes).

## Data
- **Amount now:** 1 company, 3 users (one per role), 50 customers, 8 services, 50 discovery notes,
  500 offers, about 1,460 offer items. More offers and notes are added through the app (`create-offer`, `add-note`).
- **How generated:**
  - `seed.sql`: written by hand (company, services with realistic prices, 2 example customers, test user).
  - `seed_generated.sql`: generated in SQL with `generate_series` and `random()`; the script was written
    with AI assistance (Claude). `setseed` makes it reproducible. Offers are spread over customers,
    users, statuses and 2026; every offer has 1–8 items, prices are copied from `services`.
  - All names are fictional. No real customer data is stored.
- **Effect on indexes:** with 500 offers PostgreSQL uses `idx_offers_customer_id` for
  `WHERE customer_id = …` (`EXPLAIN` shows a bitmap index scan instead of a sequential scan).
- **Expected in production:** about 100 customers with roughly 50 offers each, so about 5,000
  offers and 25,000 offer items over the agency's lifetime. Small for PostgreSQL.
