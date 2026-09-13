# Database business description

Describe business terms, table purpose, important joins, metric definitions, and
known data-quality constraints here. Database Copilot combines this description
with schema metadata read directly from the configured target PostgreSQL database.

Example:

- `public.orders` contains one row per customer order.
- Revenue means `orders.net_amount`; exclude rows where `status = 'cancelled'`.
- Join `orders.customer_id` to `customers.id`.
- All timestamps are stored in UTC.
