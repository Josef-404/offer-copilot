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
