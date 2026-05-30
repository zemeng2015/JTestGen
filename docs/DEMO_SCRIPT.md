# Demo Script

Use this when showing JTestGen to a Java engineer or Tech Lead.

## 30-second opening

JTestGen is not a generic AI test generator. It is a coverage remediation workflow for Java/Maven teams.

It starts from JaCoCo coverage data, targets a low-coverage class, builds project-aware context, generates a JUnit test, runs Maven, repairs failures, and leaves artifacts that a reviewer can inspect.

## Demo flow

1. Open the target repo and show the selected class.
2. Show the baseline coverage for that class.
3. Run JTestGen.
4. Open the generated test file.
5. Open `maven.final.log` and show Maven passed.
6. Open `summary.md` and show before/after coverage.
7. Explain that a human still reviews the PR before merge.

## Talk track

The important part is not that an LLM produced code. The important part is that the output is forced through the same workflow a Java team already trusts: Maven, coverage reports, logs, reviewable files, and source control.

For a Tech Lead, the useful result is:

- target class improved from A% to B%
- Maven passed
- generated test is available for review
- repair history and prompts are preserved

## Questions to ask after the demo

- Would this be useful for one of your low-coverage Maven repos?
- What would make this unsafe or annoying in your team?
- Would you prefer a CLI, a GitHub Action, or a manual audit PR first?
- Which report fields would a Tech Lead need before trusting the result?
- Would a paid coverage audit be easier to approve than a SaaS subscription?

## Closing ask

I am looking for 1-2 early Java/Maven teams for a small coverage audit. The goal is to pick 1-3 low-coverage classes, generate and repair tests, run Maven validation, and return a reviewable PR or patch with before/after coverage.
