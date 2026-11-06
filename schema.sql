-- Organizations that use Offer Copilot (tenants), e.g. an architecture firm
-- Security: every customer and service belongs to exactly one company, so queries can be
-- filtered by the logged-in user's company (tenant isolation)
CREATE TABLE companies (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL
);

-- People who log in to Offer Copilot
CREATE TABLE users (
    id             SERIAL PRIMARY KEY,
    company_id     INTEGER NOT NULL REFERENCES companies(id),
    email          TEXT NOT NULL UNIQUE,
    -- Security: only the Argon2id hash is stored, never the plain password
    password_hash  TEXT NOT NULL,
    -- Security: role-based access control, allowlist of roles
    role           TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'editor', 'viewer'))
);

-- Companies we write offers for
CREATE TABLE customers (
    id            SERIAL PRIMARY KEY,
    company_id    INTEGER NOT NULL REFERENCES companies(id),
    company_name  TEXT NOT NULL,
    contact_name  TEXT,
    industry      TEXT
);

-- What a company sells, with the current price
CREATE TABLE services (
    id          SERIAL PRIMARY KEY,
    company_id  INTEGER NOT NULL REFERENCES companies(id),
    name        TEXT NOT NULL,
    description TEXT,
    unit        TEXT NOT NULL,           -- e.g. 'hour', 'flat', 'month'
    unit_price  NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0)
);

-- Raw notes from a sales call
CREATE TABLE discovery_notes (
    id           SERIAL PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    call_date    DATE NOT NULL,
    -- Security: limit size to protect DB and LLM costs (availability)
    notes        TEXT NOT NULL CHECK (char_length(notes) <= 20000)
);

-- One offer for one customer
CREATE TABLE offers (
    id           SERIAL PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    -- Security: records who created the offer (non-repudiation)
    created_by   INTEGER NOT NULL REFERENCES users(id),
    created_at   TIMESTAMP NOT NULL DEFAULT now(),
    -- Security: allowlist of valid states (input validation at DB level)
    status       TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'accepted', 'rejected'))
);

-- The line items of an offer
CREATE TABLE offer_items (
    id          SERIAL PRIMARY KEY,
    offer_id    INTEGER NOT NULL REFERENCES offers(id),
    service_id  INTEGER NOT NULL REFERENCES services(id),
    quantity    NUMERIC(10,2) NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10,2) NOT NULL   -- price copied at the moment of the offer
);
