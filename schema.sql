-- Companies we write offers for
CREATE TABLE customers (
    id            SERIAL PRIMARY KEY,
    company_name  TEXT NOT NULL,
    contact_name  TEXT,
    industry      TEXT
);

-- What Artificialist sells, with the current price
CREATE TABLE services (
    id          SERIAL PRIMARY KEY,
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
    notes        TEXT NOT NULL
);

-- One offer for one customer
CREATE TABLE offers (
    id           SERIAL PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    created_at   TIMESTAMP NOT NULL DEFAULT now(),
    status       TEXT NOT NULL DEFAULT 'draft'
);

-- The line items of an offer
CREATE TABLE offer_items (
    id          SERIAL PRIMARY KEY,
    offer_id    INTEGER NOT NULL REFERENCES offers(id),
    service_id  INTEGER NOT NULL REFERENCES services(id),
    quantity    NUMERIC(10,2) NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10,2) NOT NULL   -- price copied at the moment of the offer
);