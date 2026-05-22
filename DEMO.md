# Demo: Coverage-Guided Test Generation

This demo uses `FasterXML/jackson-core`, a real open-source Java library.

## Setup

```powershell
git clone https://github.com/FasterXML/jackson-core.git C:\tmp\jackson-core
```

Use a Maven executable available on your machine. Example:

```powershell
$env:OPENAI_API_KEY="..."
$env:PYTHONPATH="src"
```

## Run

```powershell
C:\Users\wangz\AppData\Local\Programs\Python\Python313\python.exe -m javatestgen.cli run C:\tmp\jackson-core `
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

## Artifacts

Each run writes observability artifacts under the target project:

```text
.jtestgen/runs/<run-id>/
  report.json
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

See also:

- [Architecture](docs/ARCHITECTURE.md)
- [Example report](docs/examples/jackson-core-report.json)
