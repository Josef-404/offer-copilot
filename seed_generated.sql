-- Generated test data for realistic volumes. Run after seed.sql.
-- Script written with AI assistance (Claude), reviewed by me. All names are fictional.
-- setseed makes random() reproducible: every run creates the same data.
SELECT setseed(0.42);

-- 2 more users, so there is one per role
INSERT INTO users (company_id, email, password_hash, role) VALUES
    (1, 'admin@example.com', 'placeholder-no-login-yet', 'admin'),
    (1, 'viewer@example.com', 'placeholder-no-login-yet', 'viewer');

-- 48 more customers (50 in total)
INSERT INTO customers (company_id, company_name, contact_name, industry)
SELECT 1,
       (ARRAY['Nord', 'Spree', 'Alpen', 'Rhein', 'Linden', 'Havel', 'Isar', 'Elbe'])[1 + n % 8]
           || ' ' || (ARRAY['Architects', 'Engineering', 'Interior Design', 'Construction', 'Landscape'])[1 + n % 5]
           || ' ' || n || ' GmbH',
       'Contact ' || n,
       (ARRAY['Architecture', 'Engineering', 'Interior design', 'Construction', 'Landscape architecture'])[1 + n % 5]
FROM generate_series(1, 48) AS n;

-- One discovery note per customer
INSERT INTO discovery_notes (customer_id, call_date, notes)
SELECT id,
       DATE '2026-01-05' + floor(random() * 300)::INT,
       'Discovery call with ' || company_name || ': wants to cut the time spent on writing offers.'
FROM customers;

-- 500 offers, spread over customers, creators, statuses and the year 2026
INSERT INTO offers (customer_id, created_by, created_at, status)
SELECT customer_ids[1 + floor(random() * array_length(customer_ids, 1))::INT],
       user_ids[1 + floor(random() * array_length(user_ids, 1))::INT],
       TIMESTAMP '2026-01-05' + random() * INTERVAL '310 days',
       (ARRAY['draft', 'sent', 'sent', 'accepted', 'rejected'])[1 + floor(random() * 5)::INT]
FROM generate_series(1, 500),
     (SELECT ARRAY(SELECT id FROM customers ORDER BY id) AS customer_ids,
             ARRAY(SELECT id FROM users ORDER BY id) AS user_ids) AS ids;

-- Each new offer gets a random set of services (about 3 on average) with the current price as snapshot
INSERT INTO offer_items (offer_id, service_id, quantity, unit_price)
SELECT o.id, s.id, 1 + floor(random() * 3), s.unit_price
FROM offers o
JOIN services s ON s.company_id = 1
WHERE NOT EXISTS (SELECT 1 FROM offer_items i WHERE i.offer_id = o.id)
  AND random() < 0.35;

-- Offers that got no item by chance get the AI setup, so every offer has at least one item
INSERT INTO offer_items (offer_id, service_id, quantity, unit_price)
SELECT o.id, s.id, 1, s.unit_price
FROM offers o
JOIN services s ON s.company_id = 1 AND s.name = 'AI setup'
WHERE NOT EXISTS (SELECT 1 FROM offer_items i WHERE i.offer_id = o.id);
