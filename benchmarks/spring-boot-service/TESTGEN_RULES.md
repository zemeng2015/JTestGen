# Spring Boot Service Test Rules

- Use JUnit 5.
- Prefer focused service-layer unit tests over full Spring context tests.
- Use Mockito for repository/client collaborators when existing tests use Mockito.
- Do not start a web server, database, message broker, or external service.
- Assert returned domain values and verify important side effects.
- Do not modify production source or add dependencies.
