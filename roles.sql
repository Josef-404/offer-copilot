-- Least-privilege database role for the application.
-- Run after schema.sql. Set the password separately: \password offer_copilot_app
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'offer_copilot_app') THEN
        CREATE ROLE offer_copilot_app LOGIN;
    END IF;
END
$$;

-- Security: the app may read and write data, but not delete rows or change the schema
GRANT CONNECT ON DATABASE offer_copilot TO offer_copilot_app;
GRANT USAGE ON SCHEMA public TO offer_copilot_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO offer_copilot_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO offer_copilot_app;
