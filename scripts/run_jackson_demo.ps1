param(
  [string]$TargetRoot = "C:\tmp\jackson-core",
  [string]$MavenCommand = "",
  [string]$Model = ""
)

$ErrorActionPreference = "Stop"

if (-not $env:OPENAI_API_KEY) {
  throw "OPENAI_API_KEY is not set. Set it first, for example: `$env:OPENAI_API_KEY='...'"
}

if ($Model) {
  $env:OPENAI_MODEL = $Model
}

if (-not (Test-Path $TargetRoot)) {
  git clone https://github.com/FasterXML/jackson-core.git $TargetRoot
}

$argsList = @(
  "run",
  $TargetRoot,
  "--target-class", "tools.jackson.core.io.DataOutputAsStream",
  "--test-suffix", "GeneratedTest",
  "--target-coverage", "0.80",
  "--verify-arg=-DskipITs"
)

if ($MavenCommand) {
  $argsList += @("--maven-command", $MavenCommand)
}

java-testgen @argsList
