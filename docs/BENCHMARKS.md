# Benchmarks

Benchmark results should demonstrate:

- real Java repositories
- reproducible Maven commands
- target class before/after coverage
- Maven pass/fail result
- repair attempts
- generated artifact path

Completed benchmark rows require both:

- generated test Maven validation passes
- target class line coverage improves

## Benchmark Status

| Status | Repo | Commit SHA | Maven command | Target Class | Before | After | Project Before | Project After | Repair Attempts | Generated Test Path | Artifact Path | Result |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| Completed | FasterXML/jackson-core | TBD | `mvn -q -DskipITs verify` | tools.jackson.core.io.DataOutputAsStream | 55.56% | 100.00% | 81.72% | 81.75% | 1 | `src/test/java/tools/jackson/core/unittest/io/DataOutputAsStreamGeneratedTest.java` | `.jtestgen/runs/<run-id>/` | Passed |
| Completed | Apache Commons CLI | `6f57cbe00e863a2754c4c7f0344640e27f39c494` | `mvn -q -DskipITs -Drat.skip=true verify` | org.apache.commons.cli.help.FilterHelpAppendable | 77.78% | 100.00% | 98.17% | 98.27% | 2 | `src/test/java/org/apache/commons/cli/help/FilterHelpAppendableGeneratedTest.java` | `.jtestgen/runs/20260527T001034037445Z-7b185d57/` | Passed |
| Completed | JTestGen demo legacy repo | In-repo fixture | `mvn -q verify` | com.acme.billing.InvoiceCalculator | 76.00% | 96.00% | 80.65% | 96.77% | 1 | `src/test/java/com/acme/billing/InvoiceCalculatorGeneratedTest.java` | `.jtestgen/runs/20260527T003054565084Z-f9ab8d10/` | Passed |
| Completed | Mockito-heavy service | In-repo fixture | `mvn -q verify` | com.acme.orders.OrderFulfillmentService | 61.90% | 100.00% | 66.67% | 100.00% | 0 | `src/test/java/com/acme/orders/OrderFulfillmentServiceGeneratedTest.java` | `.jtestgen/runs/20260527T003939625945Z-9140501f/` | Passed |
| Completed | Spring Boot service | In-repo fixture | `mvn -q verify` | com.acme.subscriptions.SubscriptionRenewalService | 70.83% | 95.83% | 70.00% | 90.00% | 1 | `src/test/java/com/acme/subscriptions/SubscriptionRenewalServiceGeneratedTest.java` | `.jtestgen/runs/20260528T210514683467Z-5f47ff42/` | Passed |
| Planned | multi-module Maven project once supported | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Example reports:

- [jackson-core report](examples/jackson-core-report.json)
- [commons-cli report](examples/commons-cli-report.json)
- [demo legacy repo report](examples/demo-legacy-report.json)
- [mockito-heavy service report](examples/mockito-heavy-service-report.json)
- [spring boot service report](examples/spring-boot-service-report.json)

## Benchmark Template

| Field | Value |
| --- | --- |
| Repo | |
| Commit SHA | |
| Maven command | |
| Target class | |
| Baseline class coverage | |
| Final class coverage | |
| Baseline project coverage | |
| Final project coverage | |
| Repair attempts | |
| Generated test path | |
| Artifact path | |
| Notes | |

## Planned benchmark targets

- multi-module Maven project once supported
