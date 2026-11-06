# Threat Model — Offer Copilot

> Content based on my own answers, wording edited with AI assistance (Claude).
> Some of the implemented measures (`roles.sql`, `.gitignore`, `.env.example`, `users`/`companies` tables)
> were drafted with AI assistance and reviewed and tested by me.

## Implemented security measures

| Measure | Where | Protects | Verified |
|---|---|---|---|
| Allowlist for offer status | `schema.sql` — `CHECK (status IN (...))` | Integrity | Insert with `status = 'hacked'` is rejected |
| Size limit for discovery notes | `schema.sql` — `CHECK (char_length(notes) <= 20000)` | Availability, LLM costs | Insert with 20,001 characters is rejected |
| Value checks and required fields | `schema.sql` — `CHECK`, `NOT NULL`, foreign keys | Integrity | — |
| Price snapshot per offer item | `schema.sql` — `offer_items.unit_price` | Integrity of sent offers | — |
| Role-based access control (data model) | `schema.sql` — `users.role` with `CHECK (role IN ('admin', 'editor', 'viewer'))`, default `viewer` | Authorization | Insert with `role = 'superadmin'` is rejected |
| Tenant model | `schema.sql` — `companies` table, `company_id` on `users`, `customers`, `services` | Confidentiality between companies | — |
| One account per email | `schema.sql` — `users.email UNIQUE` | Authenticity | Duplicate email is rejected |
| Creator recorded per offer | `schema.sql` — `offers.created_by` | Non-repudiation | — |
| Least-privilege database role | `roles.sql` — `offer_copilot_app` may only `SELECT`, `INSERT`, `UPDATE` | Integrity, limits damage of SQL injection | `DELETE`, `DROP TABLE` and `CREATE TABLE` are denied |
| Secrets kept out of the repo | `.gitignore` (`.env`), `.env.example` without real values | Confidentiality | Git history contains no secrets |
| Database backup with tested restore | `pg_dump -Fc` / `pg_restore` (see §8) | Availability | Restore into a fresh database succeeded |

## 1. System overview
Offer Copilot creates offer drafts for architects in the DACH region. The user enters the notes
from a discovery call (e.g. transcribed voice notes), an LLM extracts the customer's needs and
selects matching services, and the offer is calculated from the database.

**Components**
- **User (browser)** — enters notes and reviews offers
- **Web app (Python)** — business logic, validation, access control *(planned)*
- **PostgreSQL** — customers, services and prices, discovery notes, offers
- **LLM API (external provider)** — extracts needs from the notes. This is the point where
  customer data leaves the system.

## 2. Assets
| Asset | Why it needs protection |
|---|---|
| Discovery notes | Confidential information about customers and their projects |
| Services and prices | Must not be manipulated — wrong prices mean wrong offers (integrity) |
| Offers | Business data of the user and their customers |
| User accounts and passwords | `users` table exists; passwords are only stored as Argon2id hash (login itself is planned) |
| Secrets | Database password and LLM API key |

## 3. Security goals
| Goal | Meaning | In Offer Copilot |
|---|---|---|
| **Confidentiality** | Only authorized parties can **read** the data | Discovery notes are only visible to the responsible user — not to other users, and the LLM provider must not use them for training |
| **Integrity** | Data cannot be **changed** without authorization or unnoticed | Only admins can change prices. A sent offer keeps its prices thanks to the price snapshot in `offer_items.unit_price` |
| **Availability** | The system and its data are **usable when needed** | Rate limiting against bot traffic; database backups to recover from data loss |
| **Authenticity** | It can be verified that someone or something **is who they claim to be** | Login verifies the user *(planned)*; the TLS certificate proves the server is ours |
| **Non-repudiation** | Someone **cannot deny** having performed an action | Log who created an offer or set it to "sent", and when *(planned)*; strongest form: digital signature |

## 4. Entry points
<!-- Where can data or requests enter the system? (forms, API endpoints, LLM responses, DB access) -->

## 5. Authentication
**Status:** `users` table with `password_hash` ✅ · login flow ⏳ planned.

**Common methods:** password + secure hashing · 2FA / MFA (TOTP app, security key; SMS is the
weakest option because of SIM swapping) · passkeys (WebAuthn) · login via an identity provider
(OpenID Connect) · magic links (only as secure as the email account).

**Planned for Offer Copilot** — one of two options, decision open:
1. **Email + password + TOTP** — passwords hashed with **Argon2id** and a per-user salt, never
   stored in plain text; second factor via an authenticator app (TOTP).
2. **Login via an identity provider (OpenID Connect)**, e.g. Google or Microsoft — Offer Copilot stores no passwords at all; the provider
   handles login and 2FA.

After login, the user session is kept in a cookie with `HttpOnly`, `Secure` and `SameSite` set.

**OAuth 2.0 vs. OpenID Connect (relevant for option 2)**
- **OAuth 2.0** is an *authorization* protocol: a user lets an app access their data at another
  service via a short-lived **access token** with limited **scopes** — without sharing the password.
- **OpenID Connect** adds *authentication* on top: with the scope `openid`, the provider also returns
  an **ID token** — a JWT signed by the provider that states who the user is (`sub`, `email`).
- Offer Copilot would use the **Authorization Code Flow with PKCE** and verify the ID token's
  signature, issuer (`iss`), audience (`aud`) and expiry (`exp`) before creating a session.

## 6. Authorization
**Status:** data model ✅ in `schema.sql` · enforcement in the app ⏳ planned.

**Common models:** RBAC (rights attached to roles) · ABAC (rules over attributes of user, object
and context) · ReBAC (rights derived from relationships, e.g. team membership) · ACLs (per-object
lists of who may do what). OAuth 2.0 covers authorization *between* apps, not inside one.

**Offer Copilot uses RBAC plus a tenant check:**

| Role | Permissions |
|---|---|
| **admin** | everything an editor can do + manage services and prices + manage users and their roles |
| **editor** | create and edit customers, discovery notes and offers |
| **viewer** | read customers, discovery notes and offers |

- **Roles in the database:** `users.role` with `CHECK (role IN ('admin', 'editor', 'viewer'))`, default
  `viewer` (least privilege). ✅
- **Tenant isolation:** users only ever see data of **their own company**. `users`, `customers` and
  `services` carry a `company_id` ✅; every query will be filtered by the user's company ⏳ — changing
  `/offers/12` to `/offers/13` must not reveal another company's offer (broken access control).
- **Central decision point:** one access check in the backend that every request passes through —
  never only in the frontend (hiding a button is not access control).
- **Deny by default:** anything not explicitly allowed for a role is forbidden.
- **No privilege escalation:** only admins can change roles; users cannot change their own role.

## 7. Input validation
**What:** every input is checked automatically against what is expected — type, range, length,
format, allowed values, existence — and **rejected** if it does not match.

**Why:** many attacks are manipulated input (SQL injection, XSS, prompt injection); invalid data
breaks integrity (e.g. negative quantities → wrong offers); oversized input threatens availability.

**Rules:** always validate **server-side** (browser checks are only UX) · **allowlist** what is allowed
instead of blocklisting what looks dangerous · validation is **one layer** — SQL injection is
additionally prevented by parameterized queries (defense in depth).

| Input | Validation | Status |
|---|---|---|
| `offer_items.quantity` | `CHECK (quantity > 0)` in the database | ✅ |
| `services.unit_price` | `CHECK (unit_price >= 0)` in the database | ✅ |
| Required fields | `NOT NULL` constraints | ✅ |
| References (`customer_id`, `offer_id`, `service_id`) | foreign keys — referenced row must exist | ✅ |
| `offers.status` | `CHECK` — only `draft`, `sent`, `accepted`, `rejected` | ✅ |
| `discovery_notes.notes` | `CHECK (char_length(notes) <= 20000)` | ✅ |
| Discovery notes via the app | valid `call_date`, length check before the LLM call (Pydantic) | ⏳ planned |
| **LLM output** | fixed schema via Pydantic; every `service_id` must exist in the database; the LLM never sets prices | ⏳ planned |

## 8. Data protection
<!-- Q2, Q9, Q10: Encryption in transit (TLS) and at rest? Where are secrets stored? Which data goes to the LLM provider? -->

**Backup and restore** ✅
```bash
pg_dump -Fc offer_copilot -f offer_copilot.dump        # backup
createdb offer_copilot_restore && pg_restore -d offer_copilot_restore offer_copilot.dump   # restore
```
Planned: run daily via cron, store encrypted outside the server (e.g. BorgBackup).

**Secrets** ✅ — database URL and LLM API key live in `.env`, which is git-ignored.

## 9. Network & deployment
<!-- Q11: Which ports are open? Is the DB reachable from the internet? Firewall, SSH? -->

## 10. Dependencies
<!-- Which libraries and external services are used? How are they checked and patched? -->

## 11. Threats & mitigations
<!-- Q8: one row per threat. Include SQL injection, CSRF, prompt injection, broken access control, leaked secrets, data loss -->
| Threat | Impact | Mitigation | Status |
|---|---|---|---|
|  |  |  | ✅ mitigated / ⏳ planned / ❌ open |

## 12. Open risks
<!-- Q8 part 2: What is honestly still open, and why is that acceptable for now? -->
