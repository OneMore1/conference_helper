# 来源与版本

论文与固定版本记录：2026-10-07。会议规则须在实际使用时重新核查。

## S1 ResearchStudio-Idea 论文 v1
来源：https://arxiv.org/html/2607.04439v1

用途：研究范围、语料、Oral/高引用/拒稿模式构成、设计建议及评估范围；不用于预测个人接收概率。

## S2 ResearchStudio-Idea 项目说明
来源：https://raw.githubusercontent.com/microsoft/ResearchStudio/063f10088af49909e1a4a7ea8d29efe19633f34e/ResearchStudio-Idea/README.md

用途：三个原始 skill 的边界。

## S3 IdeaSpark 入口
来源：https://raw.githubusercontent.com/microsoft/ResearchStudio/063f10088af49909e1a4a7ea8d29efe19633f34e/ResearchStudio-Idea/skills/idea_spark/SKILL.md

用途：固定版本的选题执行流程，作为来源依据。

## S4 官方模式 overview（已按固定 commit 读取）
来源：https://github.com/microsoft/ResearchStudio/blob/063f10088af49909e1a4a7ea8d29efe19633f34e/ResearchStudio-Idea/skills/idea_spark/references/ideation-patterns/overview.md

用途：15 模式的定义与 ID。

## S5 Scoop-Check 入口
来源：https://raw.githubusercontent.com/microsoft/ResearchStudio/063f10088af49909e1a4a7ea8d29efe19633f34e/ResearchStudio-Idea/skills/scoop_check/SKILL.md

用途：四维近邻工作比较；本包不复用自动新颖度打分。

## S6 Agent Skills 标准
来源：https://agentskills.io/specification

用途：入口、元数据、渐进加载与目录约定。

## S7 OpenAI 官方 skills 文档
来源：https://developers.openai.com/codex/skills/

用途：本地 .agents/skills 与显式调用。

## S8 ICLR 2027 Author Guidelines
来源：https://iclr.cc/Conferences/2027/AuthorGuidelines

用途：年度规则示例，不能用于其他年份或默认未来截止日期。

## S9 ICML 2026 Author Instructions
来源：https://icml.cc/Conferences/2026/AuthorInstructions

用途：不同投稿阶段规则示例。

## S10 ResearchStudio LICENSE
来源：https://raw.githubusercontent.com/microsoft/ResearchStudio/063f10088af49909e1a4a7ea8d29efe19633f34e/LICENSE

用途：上游仓库许可说明。

## 版本钉住
采用的上游 commit 为 `063f10088af49909e1a4a7ea8d29efe19633f34e`（2026-09-21）。
S2、S3、S5、S10 按固定 commit 记录；改用其他版本时应重新审查。
S1 按 v1 解释；不要把仓库更新后的流程当作该论文原评测的实现。
本包的会议规则模板故意不预填日期、页数或 AI 使用条款；使用时必须重新核查。

## 论文、许可与规则来源
- 原文 §13.3 与 §1.1：https://arxiv.org/html/2607.04439v1
- 论文许可：https://creativecommons.org/licenses/by/4.0/
- 许可法律文本：https://creativecommons.org/licenses/by/4.0/legalcode.en
- 固定仓库许可：https://github.com/microsoft/ResearchStudio/blob/063f10088af49909e1a4a7ea8d29efe19633f34e/LICENSE
- 原仓库入口判断：https://github.com/microsoft/ResearchStudio/blob/063f10088af49909e1a4a7ea8d29efe19633f34e/ResearchStudio-Idea/skills/idea_spark/references/intake-routing.md
- Skill 格式：https://agentskills.io/specification
- Codex 安装说明：https://developers.openai.com/codex/skills/
- 非盈利不是一概合理使用（美国官方解释，仅用于说明这一边界）：https://www.copyright.gov/fair-use/

## S11 Paper X-Ray
来源：https://github.com/Wang-auspicious/paper-xray/tree/80fe6a8515d24864b71b3847bd83f963e3485a6e

用途：问题、机制、对照和边界的组织思路；固定版本与 MIT 见 source-pin.json。
