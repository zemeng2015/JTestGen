# Safety and Limits

## Safety principles

- Generated tests require human review
- Production source code is not modified
- Generated revisions are preserved
- Maven logs are preserved
- Prompt snapshots are preserved
- Reports should be used as engineering evidence, not blind approval

## Current technical limits

- Maven single-module only
- assumes JaCoCo XML exists or can be generated
- JUnit-style test generation only
- does not automatically edit pom.xml
- does not guarantee semantic correctness
- may generate brittle tests
- may overfit implementation details
- may need project-specific rules

## Recommended usage

- run on a clean branch
- review generated tests manually
- prefer service/util classes before complex integration-heavy classes
- use TESTGEN_RULES.md for project-specific style and constraints
- do not auto-merge generated tests without review
