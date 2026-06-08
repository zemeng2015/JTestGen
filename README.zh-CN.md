# JTestGen

[English](README.md) | [中文说明](README.zh-CN.md)

面向 Java 团队的 AI 覆盖率修复 Agent。

JTestGen 不是通用的“AI 写单测”工具。它的目标是把 Maven/JaCoCo 项目里的低覆盖率类，系统化地转化为可审查、可运行、Maven 验证通过的 JUnit 测试候选。

核心区别：

- Copilot 帮开发者更快写测试。
- JTestGen 帮团队系统化修复覆盖率缺口。

## 适合谁

- 有 legacy Maven 项目的 Java/Spring 团队
- 有 JaCoCo coverage gate 或覆盖率 KPI 的 Tech Lead
- 想把覆盖率提升交付为 PR/patch，而不是零散生成测试文件的团队
- 需要可审计 run artifacts 的咨询或外包团队
- 希望使用本地/BYOK/OpenAI-compatible endpoint 的团队

## JTestGen 做什么

1. 运行 baseline `mvn verify`
2. 解析 JaCoCo XML 覆盖率报告
3. 选择低覆盖率目标类，优先处理 0 coverage 或最低覆盖率类
4. 收集目标源码、sample test、覆盖率数据和项目规则
5. 构建 project-aware prompt
6. 生成 JUnit 测试候选
7. 使用 Maven 只运行生成的测试
8. 如果失败，基于 Maven 输出进入 repair loop
9. 多轮修复后重新跑覆盖率
10. 输出 `report.json`、`summary.md`、prompt、Maven log 和生成版本历史

## 当前能力

| 能力 | 状态 |
| --- | --- |
| Maven single-module 项目 | 支持 |
| JaCoCo XML 报告解析 | 支持 |
| JUnit 风格测试生成 | 支持 |
| OpenAI-compatible API | 支持 |
| Maven repair loop | 支持 |
| run artifacts | 支持 |
| benchmark harness | 支持 |
| GitHub Actions 示例 | 支持 |
| Gradle 项目 | 暂不支持 |
| Maven multi-module 映射 | 暂不支持 |
| 自动修改 `pom.xml` | 暂不支持 |

## Demo 结果

| Repo | Target Class | Before | After | Maven Result |
| --- | --- | ---: | ---: | --- |
| FasterXML/jackson-core | `tools.jackson.core.io.DataOutputAsStream` | 55.56% | 100.00% | Passed |
| Apache Commons CLI | `org.apache.commons.cli.help.FilterHelpAppendable` | 77.78% | 100.00% | Passed |
| JTestGen demo legacy repo | `com.acme.billing.InvoiceCalculator` | 76.00% | 96.00% | Passed |
| Mockito-heavy service | `com.acme.orders.OrderFulfillmentService` | 61.90% | 100.00% | Passed |
| Spring Boot service | `com.acme.subscriptions.SubscriptionRenewalService` | 70.83% | 95.83% | Passed |

完整 demo 见 [DEMO.md](DEMO.md)，benchmark 见 [docs/BENCHMARKS.md](docs/BENCHMARKS.md)。

## 快速开始

```powershell
git clone https://github.com/zemeng2015/JTestGen.git
cd JTestGen

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .

git clone https://github.com/FasterXML/jackson-core.git C:\tmp\jackson-core

$env:OPENAI_API_KEY="..."

java-testgen run C:\tmp\jackson-core `
  --target-class tools.jackson.core.io.DataOutputAsStream `
  --test-suffix GeneratedTest `
  --target-coverage 0.80 `
  --verify-arg=-DskipITs
```

预期输出形态：

```text
Selected target: tools.jackson.core.io.DataOutputAsStream
Generated test passed
Class line coverage: 55.56% -> 100.00%
Artifacts written to: .jtestgen/runs/<run-id>/
```

## 运行产物

每次运行会在 `.jtestgen/runs/<run-id>/` 下保存：

- 生成 prompt
- repair prompt
- Maven 执行日志
- 生成测试的多个 revision
- `report.json`
- `summary.md`
- before/after coverage 信息

这些产物用于人工 review、PR 描述、coverage audit 和后续复盘。

## 安全边界

- 不修改生产源码
- 生成测试写入 `src/test/java`
- 保留所有生成版本
- 保留 prompt 和 Maven log
- 生成测试必须人工 review
- 不承诺自动证明业务语义正确性

## 项目文档

- [Architecture](docs/ARCHITECTURE.md)
- [Positioning](docs/POSITIONING.md)
- [Benchmarks](docs/BENCHMARKS.md)
- [Safety and limits](docs/SAFETY_AND_LIMITS.md)
- [GitHub Actions example](docs/GITHUB_ACTIONS.md)
- [Enterprise roadmap](docs/ENTERPRISE_ROADMAP.md)

## Coverage Audit

如果你有 Maven/JaCoCo 项目的覆盖率缺口，可以：

- 本地运行 JTestGen，并查看 `.jtestgen/runs/<run-id>/report.json`
- 提交 [Coverage Audit Request issue](.github/ISSUE_TEMPLATE/coverage_audit_request.md)
- 联系作者做早期 pilot：一次 Java coverage audit + test improvement PR
