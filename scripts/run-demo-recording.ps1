param(
    [string]$Fixture = "spring-boot-service",
    [string]$TargetClass = "com.acme.subscriptions.SubscriptionRenewalService",
    [string]$MavenCommand = "C:\tmp\apache-maven-3.9.11\bin\mvn.cmd",
    [string]$DemoRoot = "C:\tmp\jtestgen-recording-demo"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$fixturePath = Join-Path $repoRoot "benchmarks\$Fixture"
$projectPath = Join-Path $DemoRoot $Fixture

if (-not (Test-Path $fixturePath)) {
    throw "Fixture not found: $fixturePath"
}

if (-not (Test-Path $MavenCommand)) {
    throw "Maven command not found: $MavenCommand"
}

if (-not $env:OPENAI_API_KEY) {
    throw "OPENAI_API_KEY is not set. Set it before running the live demo."
}

Write-Host "JTestGen recording demo"
Write-Host "Repo root: $repoRoot"
Write-Host "Fixture: $fixturePath"
Write-Host "Temp project: $projectPath"
Write-Host ""

if (Test-Path $projectPath) {
    Remove-Item -Recurse -Force $projectPath
}
New-Item -ItemType Directory -Force $DemoRoot | Out-Null
Copy-Item -Recurse $fixturePath $projectPath
Remove-Item -Recurse -Force (Join-Path $projectPath "target") -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $projectPath ".jtestgen") -ErrorAction SilentlyContinue

Write-Host "Step 1: Baseline Maven verify"
& $MavenCommand -q verify -f (Join-Path $projectPath "pom.xml")
if ($LASTEXITCODE -ne 0) {
    throw "Baseline Maven verify failed."
}

Write-Host ""
Write-Host "Step 2: Run JTestGen"
$env:PYTHONPATH = Join-Path $repoRoot "src"
$env:PYTHONIOENCODING = "utf-8"
python -m javatestgen.cli run $projectPath `
    --maven-command $MavenCommand `
    --target-class $TargetClass `
    --target-coverage 0.0 `
    --max-repairs 3 `
    --test-suffix GeneratedTest
if ($LASTEXITCODE -ne 0) {
    throw "JTestGen demo run failed."
}

$runsPath = Join-Path $projectPath ".jtestgen\runs"
$latestRun = Get-ChildItem $runsPath -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latestRun) {
    throw "No JTestGen run artifact was produced."
}

$summaryPath = Join-Path $latestRun.FullName "summary.md"
$reportPath = Join-Path $latestRun.FullName "report.json"

Write-Host ""
Write-Host "Step 3: Run artifacts"
Write-Host "Run directory: $($latestRun.FullName)"
Write-Host "Summary: $summaryPath"
Write-Host "Report: $reportPath"
Write-Host ""
Write-Host "Step 4: Human-readable summary"
Write-Host "--------------------------------"
Get-Content $summaryPath
