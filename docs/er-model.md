# ER Model

> Diagram drafted with AI assistance (Claude) from `schema.sql`, reviewed by me.

```mermaid
erDiagram
    companies ||--o{ users : "employs"
    companies ||--o{ customers : "owns"
    companies ||--o{ services : "sells"
    users ||--o{ offers : "creates"
    customers ||--o{ discovery_notes : "has"
    customers ||--o{ offers : "receives"
    offers ||--|{ offer_items : "contains"
    services ||--o{ offer_items : "is used in"

    companies {
        int id PK
        text name "NOT NULL"
    }
    users {
        int id PK
        int company_id FK "NOT NULL"
        text email "NOT NULL, UNIQUE"
        text password_hash "NOT NULL, Argon2id"
        text role "admin, editor or viewer"
    }
    customers {
        int id PK
        int company_id FK "NOT NULL"
        text company_name "NOT NULL"
        text contact_name
        text industry
    }
    services {
        int id PK
        int company_id FK "NOT NULL"
        text name "NOT NULL"
        text description
        text unit "NOT NULL"
        numeric unit_price "NOT NULL, >= 0"
    }
    discovery_notes {
        int id PK
        int customer_id FK "NOT NULL"
        date call_date "NOT NULL"
        text notes "NOT NULL, max 20000 chars"
    }
    offers {
        int id PK
        int customer_id FK "NOT NULL"
        int created_by FK "NOT NULL"
        timestamp created_at "NOT NULL, default now()"
        text status "draft, sent, accepted or rejected"
    }
    offer_items {
        int id PK
        int offer_id FK "NOT NULL"
        int service_id FK "NOT NULL"
        numeric quantity "NOT NULL, > 0"
        numeric unit_price "NOT NULL, price snapshot"
    }
```

## Relationships

| From | To | Cardinality | Via |
|---|---|---|---|
| companies | users | 1 : n | `users.company_id` |
| companies | customers | 1 : n | `customers.company_id` |
| companies | services | 1 : n | `services.company_id` |
| users | offers | 1 : n | `offers.created_by` |
| customers | discovery_notes | 1 : n | `discovery_notes.customer_id` |
| customers | offers | 1 : n | `offers.customer_id` |
| offers | offer_items | 1 : n (at least one item) | `offer_items.offer_id` |
| services | offer_items | 1 : n | `offer_items.service_id` |
| **offers** | **services** | **n : m** | junction table `offer_items` |

## Indexes

| Index | Column | Status |
|---|---|---|
| Primary key index | `id` in every table | ✅ created automatically by PostgreSQL |
| Foreign key index | `offers.customer_id` | ⏳ planned (list offers per customer) |
| Foreign key index | `offer_items.offer_id` | ⏳ planned (load items of an offer) |
| Foreign key index | `discovery_notes.customer_id` | ⏳ planned (notes per customer) |
