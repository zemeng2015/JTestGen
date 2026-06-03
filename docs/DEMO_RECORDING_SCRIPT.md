# Demo Recording Script

## Goal

Record a short product demo showing JTestGen as an AI coverage remediation workflow, not a generic test generator.

Target length: 6-8 minutes.

Primary message:

> JTestGen starts from JaCoCo coverage gaps, selects a target class, builds project-aware context, generates a JUnit test, validates it with Maven, repairs failures, and writes auditable artifacts with before/after coverage.

## Recording setup

Recommended screen layout:

- left: terminal
- right: editor opened to the target Java project and generated artifacts
- browser tab optional: GitHub README benchmark table

Before recording:

- close windows that show secrets
- do not show `OPENAI_API_KEY`
- use a clean terminal
- increase terminal font size
- verify Maven and Java are available
- verify `OPENAI_API_KEY` is set without printing it

Suggested recorder:

- OBS Studio for local recording
- Loom for quick sharing
- Clipchamp if you want a simple Windows-native flow

## Demo path

Use the in-repo Spring Boot benchmark fixture:

```text
benchmarks/spring-boot-service
```

This fixture is useful for demo because it looks like a common service-layer project:

- Spring Boot app
- `@Service`
- repository/client collaborators
- existing Mockito-style test
- JaCoCo configured
- visible coverage gap

## Timeline

### 0:00-0:45 Positioning

Show README top section.

Say:

> JTestGen is an AI coverage remediation agent for Java teams. It is not trying to replace Copilot. The workflow starts from JaCoCo coverage data, chooses a low-coverage class, generates a test with project context, validates it with Maven, repairs failures, and writes auditable artifacts.

Show benchmark table with 5 completed cases.

### 0:45-1:30 Target project

Open:

```text
benchmarks/spring-boot-service/src/main/java/com/acme/subscriptions/SubscriptionRenewalService.java
```

Say:

> This is a small Spring Boot service with repository and billing collaborators. It has existing Mockito tests, but some branches are uncovered.

Open:

```text
benchmarks/spring-boot-service/src/test/java/com/acme/subscriptions/SubscriptionRenewalServiceTest.java
```

Say:

> JTestGen uses existing tests as style examples, so the generated test can follow the project's Mockito/JUnit conventions.

### 1:30-2:15 Baseline coverage

Run the recording helper:

```powershell
.\scripts\run-demo-recording.ps1
```

Let the script show:

- copied temp project path
- baseline Maven command
- JTestGen command

Say:

> The demo runs on a temp copy so the fixture stays clean. JTestGen first runs baseline Maven verify and parses JaCoCo XML.

### 2:15-4:45 Generation and repair loop

Let JTestGen run.

Call out lines like:

```text
Selected target: com.acme.subscriptions.SubscriptionRenewalService
Generating ...
Repairing ...
Generated test passed
Running final coverage
```

Say:

> The important part is not just that an LLM generated a test. The generated test must compile and pass Maven. If it fails, JTestGen sends Maven output back into a repair prompt.

### 4:45-5:45 Before/after result

Show terminal output and then open:

```text
.jtestgen/runs/<run-id>/summary.md
```

Say:

> The run writes a human-readable summary and machine-readable report. This is what a Tech Lead can review or paste into a PR.

Point out:

- target class before/after coverage
- project before/after coverage
- repair attempts
- Maven commands
- generated test path

### 5:45-6:45 Generated test and artifacts

Open generated test:

```text
src/test/java/com/acme/subscriptions/SubscriptionRenewalServiceGeneratedTest.java
```

Open artifact folder:

```text
.jtestgen/runs/<run-id>/
```

Show:

- `prompt.initial.user.txt`
- `prompt.repair.1.user.txt` if repair happened
- `maven.test.0.log`
- `generated.initial.java`
- `generated.final.java`
- `report.json`
- `summary.md`

Say:

> The workflow is auditable. You can see exactly what prompt was sent, what Maven returned, what was generated, and what changed after repair.

### 6:45-7:30 Close

Show README CTA:

```text
Try It / Request a Coverage Audit
```

Say:

> The current product surface is CLI-first. The first offer is a coverage audit or test improvement PR for a Maven Java repo with JaCoCo coverage gaps.

## What not to claim

Do not claim:

- generated tests prove business correctness
- JTestGen works on every Java project
- JTestGen replaces human review
- JTestGen automatically edits production code
- JTestGen is already a full QA platform

Do claim:

- generated tests are Maven-validated candidates
- coverage improvement is measurable
- artifacts make the workflow reviewable
- project rules and sample tests guide generation

## Short version

If you need a 90-second demo:

1. Show README positioning and benchmark table.
2. Run `.\scripts\run-demo-recording.ps1`.
3. Show selected target and final coverage delta.
4. Open `summary.md`.
5. Open generated test.
6. State that human review is still required.
