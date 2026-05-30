# Outreach Notes

Use these messages for former colleagues, trusted Java engineers, or small-team Tech Leads.

## Short LinkedIn / Slack message

Hi [Name], I am building JTestGen, an AI-assisted coverage remediation workflow for Java/Maven projects.

It is not a generic test generator. It targets low-coverage classes from JaCoCo, generates JUnit tests, runs Maven, repairs failures, and produces a reviewable PR-style summary with before/after coverage.

I am looking for 1-2 real Java repos for an early coverage audit. If you have a Maven project with coverage gaps, I would love to try it on 1-3 classes and share the results. No need to share private code publicly; a local run or sanitized repo works too.

## More direct pilot ask

I am testing a small service offer around JTestGen:

- identify 1-3 low-coverage classes
- generate and repair tests
- run Maven validation
- provide before/after coverage
- deliver a reviewable PR or patch

For early pilots, I am aiming for a small `$100-$300` audit only if the result is useful. Would you be open to letting me try it on one Maven repo or a small module?

## Follow-up after interest

Great. To see whether JTestGen is a fit, I need:

- Java version
- Maven command used by CI
- JaCoCo XML report path, if already available
- 1-3 packages or classes you care about, if any
- testing constraints or team rules

If the repo is private, you can run the CLI locally and share only `report.json`, `summary.md`, and high-level coverage numbers.

## What not to promise

- Do not promise arbitrary Java project support.
- Do not promise semantic correctness without human review.
- Do not promise automatic merge-ready tests.
- Do not claim it replaces developers or QA.

Promise the narrower, stronger result: Maven-validated, reviewable test improvement artifacts for reproducible Maven + JaCoCo projects.
