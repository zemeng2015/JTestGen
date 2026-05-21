# Java TestGen Repair

`java-testgen` is a local CLI for generating Java unit tests from JaCoCo coverage gaps, running the generated test, and repairing it when Maven reports failures.

The first version is intentionally small and inspectable. It targets Maven projects that use JUnit and JaCoCo, and delegates test writing to an OpenAI-compatible chat completion endpoint.

## Quick Start

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -e .

$env:OPENAI_API_KEY="..."
java-testgen run C:\path\to\java-project --target-coverage 0.80 --max-repairs 3
```

By default, the CLI calls `https://api.openai.com/v1/chat/completions` with `gpt-4o-mini`. You can override:

```powershell
$env:OPENAI_BASE_URL="https://your-compatible-endpoint/v1"
$env:OPENAI_MODEL="your-model"
```

## What It Does

1. Runs baseline coverage with `mvn -q verify`.
2. Parses `target/site/jacoco/jacoco.xml`.
3. Selects the most uncovered class, prioritizing classes with 0 covered lines.
4. Finds the target source file under `src/main/java`.
5. Collects existing sample tests from `src/test/java`.
6. Loads project-specific generation rules from `--rules-file`, `TESTGEN_RULES.md`, `.testgen-rules.md`, or built-in defaults.
7. Builds a prompt with coverage data, source code, sample tests, and rules.
8. Writes one generated JUnit test under `src/test/java`.
9. Runs only the generated test with `mvn -q -Dtest=<GeneratedTestClass> test`.
10. If it fails, sends the generated test, source code, sample tests, rules, and Maven output back to the model for repair.
11. Repeats until the generated test passes or the repair limit is reached.
12. Runs final coverage with `mvn -q verify` and reports project and target-class coverage before/after.

## Assumptions

- The target project uses Maven.
- Maven is available on `PATH`.
- The target project has or can resolve test dependencies.
- Generated tests are JUnit 5 by default.
- JaCoCo report generation is available through the Maven JaCoCo plugin.

## Commands

Generate one coverage-guided test and run the repair loop:

```powershell
java-testgen run C:\path\to\java-project
```

Dry-run prompts without writing files or running Maven:

```powershell
java-testgen run C:\path\to\java-project --dry-run
```

Useful options:

```text
--class-glob        Glob under src/main/java, default **/*.java
--target-coverage  Minimum line coverage ratio, default 0.80
--max-repairs      Repair attempts for the generated test, default 3
--sample-tests      Existing test files to include as examples, default 3
--rules-file        Optional file containing project-specific rules
--test-suffix      Generated test class suffix, default Test
--model            Override OPENAI_MODEL
```

## Project Rules

You can add a rules file to the target Java repo:

```text
TESTGEN_RULES.md
```

Example:

```text
- Use AssertJ assertions.
- Do not use Mockito for value objects.
- Prefer @ExtendWith(MockitoExtension.class) for mocks.
- Keep tests package-private.
```

## Notes

This tool writes generated tests into the target Java project. Use source control in the target project so you can review and keep only the useful tests.
