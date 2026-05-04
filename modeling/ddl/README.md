# DDL excerpts

Hand-authored DDL for representative subdomains. Used as the contract that
dbt models materialize to and as documentation for downstream consumers.

For now we ship Payments only:

- `payments_3nf.sql` — operational 3NF schema.
- `payments_vault.sql` — Data Vault 2.0 hubs/links/satellites.
- `payments_dim.sql` — analytical star schema.

Other subdomains will get the same treatment in subsequent phases.
