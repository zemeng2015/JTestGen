# Strategy

## 90-day objective

Get one real Java team to try JTestGen on a real Maven repository and complete one measurable coverage audit or test improvement PR.

This is intentionally smaller than building a platform. The goal is to prove that a team cares enough about coverage remediation to share a repo, run the workflow, review the generated tests, and consider paying for the result.

## First user profile

The first user should be a Java/Spring Tech Lead at a small or mid-sized team.

Good signs:

- owns a Maven Java or Spring Boot codebase
- has JaCoCo coverage gaps or a coverage KPI
- has legacy service/util classes with weak unit tests
- can run the project locally or in CI
- cares about reviewable PRs, not blind auto-merge
- is willing to share feedback on generated test quality

Best first channels:

1. warm intros from former coworkers or friends
2. Java/Spring teams in the user's network
3. maintainers of smaller public Maven projects
4. small consulting or outsourcing teams with coverage delivery work

Cold outreach to unknown companies should come later, after the offer and benchmark story are sharper.

## Wedge

Coverage remediation for Maven Java teams that already use or can generate JaCoCo XML.

JTestGen should not compete head-on with general coding assistants. The wedge is the workflow around coverage gaps:

- choose the target from coverage data
- build project-aware prompt context
- generate the test
- validate with Maven
- repair failures
- preserve auditable artifacts
- report before/after coverage

## Initial offer

Start with a service-assisted offer:

Coverage Audit + Test Improvement PR

- identify low-coverage classes
- select 1-3 AI-fixable targets
- generate at least one Maven-passing test candidate
- provide before/after coverage numbers
- deliver generated tests as a branch, patch, or PR
- include run artifacts for review

Suggested first paid range: `$100-$300`.

The point is not revenue scale yet. The point is to test whether teams value the outcome enough to pay for a concrete coverage improvement.

## Product shape

Short term:

- open-source CLI
- service-assisted audit package
- example benchmark reports
- optional GitHub Actions workflow example

Medium term:

- CLI batch mode
- PR/patch generation mode
- improved report summary
- GitHub Action wrapper

Do not start with SaaS or Web UI. The first product surface should live where Java teams already work: local repos, Maven, CI, and pull requests.

## Success metric

The strongest proof is not downloads or stars. It is:

- a real repo
- a real coverage gap
- a generated test that passes Maven
- a before/after coverage delta
- a human-reviewed PR or patch
- feedback from a Tech Lead or maintainer

Primary 90-day target:

- 1 real team/user completes a coverage audit or test improvement PR

Secondary targets:

- 5 completed benchmark cases
- 3-5 warm outreach conversations
- 1 public technical article
- 1 repeatable GitHub Actions example

## Public story

Recommended article angle:

> I used AI to improve test coverage in a legacy Maven project, but forced it through JaCoCo targeting, Maven validation, and repair loops.

Core message:

General AI coding tools can write tests. JTestGen is about making coverage remediation measurable, repeatable, and reviewable.

## Main risks

### "It only works on toy projects"

Mitigation:

- keep adding real benchmarks
- clearly mark completed and failed attempts
- publish exact Maven commands and target classes
- include run artifacts and reports

### "Generated tests are low quality"

Mitigation:

- position outputs as reviewable candidates
- show Maven validation and repair loop
- support `TESTGEN_RULES.md`
- keep production source unchanged
- preserve prompts, generated revisions, and logs

### "Configuration is too hard"

Mitigation:

- document the minimum Maven/JaCoCo assumptions
- provide audit request template
- create a GitHub Actions example
- add clearer failure messages and report summaries

### "This is no different from Copilot"

Mitigation:

- emphasize coverage-guided target selection
- show before/after coverage deltas
- show Maven logs, repair attempts, and artifacts
- sell workflow evidence, not code completion

## 90-day roadmap

### Days 1-30

- complete 5 benchmark cases
- improve benchmark documentation and report examples
- finish one Spring Boot service demo benchmark
- write first technical article draft
- prepare a short coverage audit outreach message

### Days 31-60

- contact 3-5 warm Java/Spring leads
- run 1-2 free coverage audits
- improve report summary based on feedback
- add batch mode for multiple target classes
- create GitHub Actions example workflow

### Days 61-90

- convert one audit into a paid or trial-paid coverage improvement PR
- add PR/patch generation mode
- write a case study if permission is granted
- refine paid package scope and pricing
- decide whether GitHub Action should become the next product surface

## Decision rule

If a team will not review or pay for a small coverage improvement PR, do not build a larger platform yet.

If one team does pay or seriously engages, double down on the CLI + PR workflow before building dashboards or SaaS.
