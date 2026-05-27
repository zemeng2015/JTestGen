# Mockito-heavy Service Test Rules

- Use JUnit 5 and Mockito.
- Follow existing tests using `@ExtendWith(MockitoExtension.class)`.
- Mock collaborators instead of using fake network, database, or queue implementations.
- Verify important repository/client interactions when behavior depends on side effects.
- Do not add dependencies or modify production source.
- Keep tests focused on `OrderFulfillmentService`.
