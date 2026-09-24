# Target repository to draft PR

`contribute` clones a GitHub repository into a **new** workspace, runs the existing
generation/repair workflow, and prepares a verifiable contribution manifest.
It never modifies your existing checkout. Publishing is explicit and always creates
a draft PR; it never merges or force-pushes.

```sh
java-testgen contribute owner/repo --workspace ./contribution-001 \
  --target-class example.Target --jacoco --target-coverage 0

# Review repo/ changes, contribution.json, pr-summary.md and local run evidence.
java-testgen publish ./contribution-001/contribution.json
```

For an unattended end-to-end run, append `--create-pr` to `contribute`. This is
authorization to create a fork, local commit, remote branch and public draft PR.
Review the target repository's contribution and AI policies before doing so.
Maven executes the target repository's build plugins; use repositories you trust
and an appropriately isolated environment.

## Prerequisites and scope

- Python 3.10+, Git, the target project's JDK and Maven, and a working generator.
- For publishing, GitHub CLI (`gh`) authenticated with repository/fork/PR access,
  Git credentials configured for HTTPS pushing, and Git commit name/email.
- Default generation uses the existing OpenAI-compatible API environment.
  `--generator codex` uses the locally authenticated Codex CLI instead.
- Input is `owner/repo` or a credential-free `https://github.com/owner/repo` URL.
- Only one target and one Maven module are supported. Use `--module core` to
  select a repository-relative module with its own `pom.xml`; reactor dependency
  resolution and cross-module coverage aggregation are not automated.
- The project must produce `target/site/jacoco/jacoco.xml`. `--jacoco` explicitly
  invokes pinned JaCoCo 0.8.14 `prepare-agent`, then `verify`, then `report` without
  changing a POM. Project-specific incompatible plugins still need resolution.
- `--target-coverage` is the existing **project** line-coverage threshold. Setting
  it to zero does not disable contribution quality gates: target coverage must
  strictly improve, project coverage cannot regress, all checks must pass.
- Default suffix is `JTestGenTest`; choose another `--test-suffix` if it collides
  with an existing test. Existing test files are not overwritten by this mode.
- No external dependency is added. Existing `run`, `scan` and `doctor` retain
  their behavior; `run` also accepts `--generator` and `--jacoco`.

## Evidence and publication gates

The workspace contains `repo/`, `contribution.json`, and `pr-summary.md`.
Local prompts, Maven output, revisions, and report files stay under the selected
project's `.jtestgen/runs/`; they are never staged or included in PR text.

The manifest binds repository origin, base SHA/branch, selected module, provider,
requested/resolved model, report SHA-256, and generated Java file SHA-256. Publish
checks all of them against the checkout. It requires successful baseline,
generated-test and final verification, measurable target improvement, and a diff
containing exactly the verified Java test file. Extra source/configuration changes,
staged files outside that test, changed tests/reports and unexpected HEAD commits
block publishing. After editing tests, prepare a new verified run.

The public summary reports measured coverage, base commit, module, verification
commands, repair count and AI provenance. Commands normalize the Maven executable
and explicitly label their redacted outline, omitting extra local arguments to avoid leaking paths or secrets. It explicitly
calls for human review and does not claim semantic correctness or acceptance.
Editing `pr-summary.md` does not override this generated summary: publishing
regenerates it from the bound report.

Publishing uses the authenticated user's fork, validates its upstream parent,
pushes the recorded commit without force, and creates a draft PR. Receipts are
saved back to the manifest. Retry `publish` after an uncertain network response:
it checks for an existing PR on the same head branch and commit before creating
anything. A closed/merged PR or changed head is refused, not duplicated. A
manually changed local branch/commit may require a new preparation. Failed
preparation retains a failure manifest and any local run artifacts; select a
new workspace for the next attempt.

The manifest guards accidental changes; it is not a signature or a security
boundary against someone who can edit both the checkout and manifest.

## Validation

Run `python -m unittest discover -s tests`. Publication tests use real temporary
Git repositories for diff/index/hash/commit checks and mock all network actions.
They verify refusal of tampered tests/reports, production changes, coverage
regressions, skipped tests, unsafe repository/module names, plus recovery from a
PR successfully created remotely whose response was lost. No test pushes or
opens a live PR.

Contribution mode clears only the known JaCoCo XML/exec evidence files before
baseline and final checks, matching Surefire reports before each generated-test
check, and Surefire reports before final verification. It requires fresh,
non-skipped executed test cases, including the generated class in the final suite.
Symlink/junction paths are rejected before artifact writes and cleanup. The actual
Git commit's tree and blob bytes are validated before push so hooks or clean
filters cannot silently publish a different file than the verified candidate.
The isolated clone uses `core.autocrlf=input` from the initial checkout: a Maven
formatter writing native CRLF on Windows does not make unchanged source files
appear modified. Commit validation permits only CRLF-to-LF normalization of the
verified test bytes. Other whitespace/content changes and arbitrary clean-filter
transformations remain blocked; local manifest SHA-256 still binds exact bytes.
