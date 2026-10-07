# Conference Helper

从研究方向、模型设计或已有结果开始，推进本轮科研任务。技能入口是 `$conference-helper`，项目版本为 0.1.0。

## 直接开始

```text
使用 $conference-helper。
我想研究一个 fMRI 基座模型方向，先推荐具体问题和最小验证。
```

也可以说“模型设计已经完成，帮我安排有必要的 ablation”或“把已有结果组织成文章”。提供当前材料即可；不要求先填 JSON 或走完整套阶段。

[三个教学案例](examples/research-workflow-cases.md) · [研究 Tips](references/review-tips.md) · [消融计划](assets/ablation-plan.md) · [贡献核对](assets/contribution-check.md)

## 思考路线

具体问题 → 设计理由 → 证据和竞争解释 → 下一步或写作交付。ResearchStudio-Idea 的录用/拒稿案例启发会被映射到贡献句、对照和结论范围；它们不用于估算录用概率。文献为当前研究提供依据，不设独立论文解读入口。

本地项目记录是可选的。需要时运行 `python scripts/workflow.py --help`，由 agent 根据已有材料填写并保存；状态记录与科学判断分别核对。

## 安装与内容

将本目录完整放到研究项目 `.agents/skills/conference-helper/`，保留所有资源和许可文件。完整源码包中的 `tools/install_skill.py` 提供拒绝覆盖与升级备份。

- references/：研究阶段规则、Tips 与来源。
- assets/：按需使用的记录和交付模板。
- examples/：合成教学案例。
- scripts/：离线状态与检查工具，Python 3.10+ 标准库。
- evals/：机械检查与评估说明。

联网检索、远程执行和编译由宿主提供。科研作业、外部写入和实际投稿需要用户授权。没有回执不能标记已提交。

[许可范围](LICENSE-SCOPE.md) · [来源声明](THIRD_PARTY_NOTICES.md) · [来源版本](source-pin.json)
