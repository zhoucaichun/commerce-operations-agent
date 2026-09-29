CREATE TABLE IF NOT EXISTS commerce_sessions (thread_id TEXT PRIMARY KEY, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS commerce_tickets (idempotency_key TEXT PRIMARY KEY, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS commerce_metrics (name TEXT PRIMARY KEY, value BIGINT NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS commerce_metric_snapshots (bucket TIMESTAMPTZ NOT NULL, name TEXT NOT NULL, value BIGINT NOT NULL, PRIMARY KEY (bucket, name));
CREATE TABLE IF NOT EXISTS commerce_products (sku TEXT PRIMARY KEY, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS commerce_policies (policy_id TEXT PRIMARY KEY, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS commerce_orders (order_id TEXT PRIMARY KEY, payload JSONB NOT NULL);
INSERT INTO commerce_products VALUES
('AC-65W','{"sku":"AC-65W","name":"65W USB-C PD Charger","category":"charger","power_w":65,"ports":["USB-C"],"regions":["CN","US","EU"],"stock":"simulated_available"}'),
('AC-100W','{"sku":"AC-100W","name":"100W USB-C PD Charger","category":"charger","power_w":100,"ports":["USB-C"],"regions":["CN","US","EU"],"stock":"simulated_available"}'),
('CB-C2C-2M','{"sku":"CB-C2C-2M","name":"2m USB-C to USB-C Cable","category":"cable","power_w":100,"ports":["USB-C","USB-C"],"regions":["CN","US","EU"],"stock":"simulated_low"}') ON CONFLICT DO NOTHING;
INSERT INTO commerce_policies VALUES
('return-cn-2026-01','{"policy_id":"return-cn-2026-01","topic":"return","region":"CN","effective_from":"2026-01-01","summary":"Synthetic policy: unopened accessories may be requested for return within 7 days.","source":"postgres_synthetic_seed"}'),
('warranty-cn-2026-01','{"policy_id":"warranty-cn-2026-01","topic":"warranty","region":"CN","effective_from":"2026-01-01","summary":"Synthetic policy: eligible chargers and cables have a 12-month limited warranty.","source":"postgres_synthetic_seed"}') ON CONFLICT DO NOTHING;
INSERT INTO commerce_orders VALUES ('ORD-10023','{"order_id":"ORD-10023","identity_suffix":"4821","status":"shipped","sku":"AC-65W","quantity":1,"purchased_on":"2026-09-10","shipment":{"carrier":"Simulated Express","tracking_number":"SIM-TRK-10023","last_event":"Handed to local carrier","estimated_delivery":"2026-09-29"}}') ON CONFLICT DO NOTHING;
