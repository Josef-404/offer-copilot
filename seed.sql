-- Services Artificialist offers
INSERT INTO services (name, description, unit, unit_price) VALUES
    ('AI setup', 'One-time setup of an AI workflow', 'flat', 2000.00),
    ('Monthly retainer', 'Ongoing support and improvements', 'month', 500.00);

-- Example customers for testing
INSERT INTO customers (company_name, contact_name, industry) VALUES
    ('Example Architects GmbH', 'Anna Example', 'Architecture'),
    ('Example Engineering GmbH', 'Ben Example', 'Engineering');