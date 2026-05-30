# GitHub Actions Example

JTestGen is still intended to run locally first. Use GitHub Actions only after `doctor` and `scan` work on the target repository.

## Recommended first workflow

Copy [.github/examples/jtestgen-audit.yml](../.github/examples/jtestgen-audit.yml) into the target repository as:

```text
.github/workflows/jtestgen-audit.yml
```

The workflow has two jobs:

- `scan`: runs `java-testgen doctor .` and `java-testgen scan . --top 10`
- `generate`: optionally runs `java-testgen run . --target-class ...` when a class is provided manually

## Required secret

For generation, add this repository secret:

```text
OPENAI_API_KEY
```

The scan job does not call an LLM and does not need an API key.

## Usage guidance

Start with manual `workflow_dispatch`. Do not auto-run generation on every PR until the team agrees on review rules.

Generated tests should be treated as reviewable candidates. Maven success and coverage improvement do not prove business correctness.
