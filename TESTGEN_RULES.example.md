# JTestGen Project Rules Example

- Generate JUnit 5 tests unless existing tests use JUnit 4.
- Prefer simple deterministic unit tests.
- Do not modify production source code.
- Do not add new dependencies.
- Use existing test style when available.
- Prefer meaningful assertions over smoke tests.
- Avoid testing private methods directly.
- Avoid brittle timing, network, filesystem, or environment assumptions.
- Use Mockito only when existing project tests already use Mockito.
- Keep generated tests focused on the target class.
