# Demo Legacy Repo Test Rules

- Use JUnit 5.
- Keep tests deterministic and focused on public behavior.
- Prefer clear assertions on returned values.
- Do not add dependencies or modify production source.
- Do not test private methods directly.
- For `InvoiceSummary.total`, remember the production formula is subtotal minus discount plus tax.
- When Maven reports a deterministic expected/actual mismatch, update the expected value to match the production formula and Maven actual output.
