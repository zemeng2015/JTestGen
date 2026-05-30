# Demo: Coverage-Guided Test Improvement

This demo uses `FasterXML/jackson-core`, a real open-source Java library.

The goal is to show the full workflow:

1. target one low-coverage class
2. generate a JUnit test
3. run Maven validation
4. repair failures when needed
5. leave reviewable coverage and run artifacts

## Setup

```powershell
git clone https://github.com/zemeng2015/JTestGen.git
cd JTestGen

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .

git clone https://github.com/FasterXML/jackson-core.git C:\tmp\jackson-core
```

Set your API key:

```powershell
$env:OPENAI_API_KEY="..."
```

Optional model override:

```powershell
$env:OPENAI_MODEL="gpt-4o-mini"
```

## Run

If Maven is already on your `PATH`, run:

```powershell
java-testgen run C:\tmp\jackson-core `
  --target-class tools.jackson.core.io.DataOutputAsStream `
  --test-suffix GeneratedTest `
  --target-coverage 0.80 `
  --verify-arg=-DskipITs
```

If Maven is not on your `PATH`, pass the executable explicitly:

```powershell
java-testgen run C:\tmp\jackson-core `
  --target-class tools.jackson.core.io.DataOutputAsStream `
  --test-suffix GeneratedTest `
  --target-coverage 0.80 `
  --maven-command C:\tmp\apache-maven-3.9.11\bin\mvn.cmd `
  --verify-arg=-DskipITs
```

## Observed Result

```text
Selected target: tools.jackson.core.io.DataOutputAsStream with 55.56% line coverage
Repairing DataOutputAsStreamGeneratedTest, attempt 1/3
Generated test passed

Generation report
- Target class: tools.jackson.core.io.DataOutputAsStream
- Class line coverage: 55.56% -> 100.00%
- Class covered lines: 5/9 -> 9/9
- Project line coverage: 81.72% -> 81.75%
```

## What to Show in a Demo

When presenting JTestGen, do not describe it as "AI generated a test." The stronger message is:

> JTestGen turns a Java coverage gap into a Maven-passing, reviewable test improvement artifact.

Show these four things:

1. the target class and baseline coverage
2. the generated test file
3. Maven pass/fail logs and repair attempts
4. `summary.md` with before/after coverage

## Artifacts

Each run writes observability artifacts under the target project:

```text
.jtestgen/runs/<run-id>/
  report.json
  summary.md
  prompt.initial.system.txt
  prompt.initial.user.txt
  prompt.repair.1.system.txt
  prompt.repair.1.user.txt
  maven.baseline.log
  maven.test.0.log
  maven.test.1.log
  maven.final.log
  generated.initial.java
  generated.repair.1.java
  generated.final.java
```

These files make the LLM workflow inspectable and reproducible.

## Clean Up

The demo writes a generated test into the target repo. If you want to reset `jackson-core` afterward:

```powershell
cd C:\tmp\jackson-core
git status
git clean -fd .jtestgen
git restore src/test/java
```

See also:

- [Architecture](docs/ARCHITECTURE.md)
- [Example report](docs/examples/jackson-core-report.json)
- [Demo script](docs/DEMO_SCRIPT.md)
