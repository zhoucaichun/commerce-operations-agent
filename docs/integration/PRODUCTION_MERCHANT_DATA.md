# Production merchant data integration

## Current status

Not implemented. The current PostgreSQL/SQLite stores and catalogue are synthetic demonstration data only. Dify remains a workflow and evaluation reference, not a database or production connector.

## Required production design

1. Each merchant receives an organization and `tenant_id`; all product, policy, order, ticket, attachment and audit records use tenant-scoped PostgreSQL tables with row-level security.
2. Shopify is the first connector: OAuth installation, encrypted per-merchant tokens in a secret manager, webhook signature verification, idempotent event ingestion, and a read-only catalogue/order projection.
3. Agent tools query the local tenant projection rather than arbitrary merchant databases. Inventory, refund, cancellation and address mutation remain disabled until separately approved.
4. A merchant administrator configures field mappings, sync scope, retention, roles and consent. Support staff never receive raw database credentials.
5. Before activation: contract/DPA, security review, sandbox verification, least-privilege scopes, audit logs, deletion/export procedures, backup recovery drill, alerting, and rollback.

## Dify role

The exported Dify classifier prompts, route graph and badcase/evaluation datasets are retained as reference material. They are translated into Commerce Agent route tests and prompts; they do not replace tenant data, authorization, connectors, or controlled tools.
