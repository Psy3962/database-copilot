# Database assistant

The assistant answers a business question through two bounded tools:

1. `get_database_context` introspects configured PostgreSQL schemas and appends
   the human-maintained `database_description.md`.
2. `run_readonly_query` executes one generated statement in a transaction set to
   `READ ONLY`, with a statement timeout and row limit.

Successful query results are registered for the current turn. The structured
`DatabaseAnswer.query_id` must reference one of those results or validation fails
closed and no assistant message is persisted.

The target database connection is separate from the product database that stores
users and chat history. Configure it with `TARGET_DATABASE_URL`, using a dedicated
PostgreSQL role that has only `CONNECT`, `USAGE`, and `SELECT` grants.
