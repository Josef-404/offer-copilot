-- Company using Offer Copilot
INSERT INTO companies (name) VALUES
    ('Artificialist');

-- Services Artificialist offers
INSERT INTO services (company_id, name, description, unit, unit_price) VALUES
    (1, 'AI setup', 'One-time setup of an AI workflow', 'flat', 2000.00),
    (1, 'Monthly retainer', 'Ongoing support and improvements', 'month', 500.00);

-- Example customers for testing
INSERT INTO customers (company_id, company_name, contact_name, industry) VALUES
    (1, 'Example Architects GmbH', 'Anna Example', 'Architecture'),
    (1, 'Example Engineering GmbH', 'Ben Example', 'Engineering');

-- More services, so the knapsack optimizer has real choices (2^8 = 256 combinations)
INSERT INTO services (company_id, name, description, unit, unit_price) VALUES
    (1, 'Process analysis', 'Map the current offer process and find time sinks', 'flat', 1200.00),
    (1, 'Workshop', 'Half-day AI workshop for the team', 'flat', 800.00),
    (1, 'Custom integration', 'Connect the CRM or project software', 'flat', 3000.00),
    (1, 'Training session', 'One training session for new users', 'flat', 400.00),
    (1, 'Reporting dashboard', 'Dashboard with offer statistics', 'flat', 1500.00),
    (1, 'Data cleanup', 'Clean up existing customer and service data', 'flat', 900.00);

-- Test user, needed because every offer records its creator (offers.created_by).
-- Placeholder instead of a real Argon2id hash: login is not implemented yet.
INSERT INTO users (company_id, email, password_hash, role) VALUES
    (1, 'test@example.com', 'placeholder-no-login-yet', 'editor');
