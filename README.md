# Conference Helper

**把研究方向变成问题，把模型设计变成证据，把已有结果组织成文章。**

从顶会论文的研究经验中提炼可执行的建议，服务选题、实验论证、写作与投稿准备。一个 Skill，按你的当前任务进入。

**v0.1.0 · 首次开源发布** · **Python 3.10+** · **MIT / CC BY 4.0（来源归纳）** · [English](README.en.md)

[开始使用](#开始使用) · [研究 Tips](#来自原研究的中稿启发) · [完整案例](skills/conference-helper/examples/research-workflow-cases.md) · [用户手册](docs/USER_GUIDE.zh-CN.md)

## 你现在需要哪一种帮助

| 你可以直接说 | Skill 应交付什么 | 示例 |
|---|---|---|
| **我想研究一个 fMRI 基座模型方向的工作** | 具体问题、候选切入点与取舍、推荐主线、最小验证 | [从方向开始](skills/conference-helper/examples/research-workflow-cases.md#1-我想研究一个-fmri-基座模型方向的工作) |
| **我已经完成模型设计，还需要增加哪些 ablation** | 核心论断、证据缺口、匹配对照、不同结果的含义与优先级 | [为模型补证据](skills/conference-helper/examples/research-workflow-cases.md#2-模型设计完成后续需要哪些-ablation) |
| **如何把我们的结果整理成一篇文章** | 文章主线、论断与图表对应、章节提纲、有依据的示范文字 | [从结果成文](skills/conference-helper/examples/research-workflow-cases.md#3-如何把已有结果整理成文章) |

只提供当前已有的信息即可：方向一句话也能开始；有模型说明或结果时直接读取。补充问题仅限会改变本轮判断的内容，用户无需先填写 JSON 或选择阶段。

三个案例采用合成的 fMRI 场景。示例中的部件、数值和推荐均是教学设定，不是用户实际模型、真实实验或新颖性结论。

## 来自原研究的中稿启发

[ResearchStudio-Idea](https://arxiv.org/abs/2607.04439v1) 分析了 1,947 篇 ML 论文，包含 Oral、高引用与拒稿样本。Conference Helper 把其中的经验观察和设计建议转成具体研究动作：

| Tip | 怎样落实到你的研究 |
|---|---|
| **一句话说清贡献** | 说明在什么条件下，构造、测量或证明了什么，以及相对最近邻的差异 |
| **部件各有分工** | 每个设计对应一个瓶颈；声称组合收益时才检验相互作用 |
| **让先验的作用可识别** | 对结构先验使用合理替代或错配对照，核对容量和训练预算 |
| **近邻差异落到实质** | 比较问题、机制、见解和范围，避免仅换名称或换应用场景 |
| **指标测到主张的能力** | 分开性能、机制和内部统计，不把代理指标当最终证据 |
| **提前写失败条件** | 明确哪项结果会削弱解释，以及何时停止扩展实验 |
| **结论范围跟着证据走** | 用图表支撑主线，保留负结果，写清适用条件 |

每条 Tip 的[原文位置、适用条件与执行方式](skills/conference-helper/references/review-tips.md)都有记录。Skill 会选取与当前任务有关的提示，落实到贡献句、消融或文章结构中。

这些启发不构成接收概率预测。原文的 Oral/Reject 样本比例不是普通投稿接收率；选题、消融与写作中的操作映射是本项目的扩展。

## 开始使用

准备 Python 3.10+，在已解压或克隆的源码目录运行：

~~~bash
python tools/install_skill.py --project /path/to/your-paper-project
~~~

<details>
<summary>Windows 与升级</summary>

将源码包解压到较短目录，并把自己的研究目录传给安装器：

~~~powershell
python "C:\Tools\conference_helper\tools\install_skill.py" --project "D:\Research\my-paper"
~~~

已有安装升级时增加 --backup-existing，旧 Skill 会备份到扫描目录之外。[完整安装方法](docs/USER_GUIDE.zh-CN.md)

</details>

在 Codex 中打开研究目录，新建对话。以下三种请求按需要任选，不必依次走完。

### 只有一个大概方向

~~~text
使用 $conference-helper。
我想研究一个 fMRI 基座模型方向的工作，目前只有大概方向。
请比较可能的切入点，推荐一个具体问题，说明理由、关键未知项和最小验证。
先简短讲清楚，不启动实验。
~~~

它会先把“做什么模型”细化成“希望解决什么问题、怎样判断是否解决”。数据或预算不确定，可以直接说明；不会把建议写成你已经做出的决定。

### 已有模型，想补消融

~~~text
使用 $conference-helper。
我已经完成模型设计，后续还需要增加哪些 ablation？
设计说明：[粘贴说明或给文件路径]；已有实验：[有则提供]。
请把核心论断对应到缺少的证据，说明每项对照改变什么、保持什么、
不同结果说明什么，并按必要程度与成本排序。不启动实验。
~~~

先检查已有证据，再推荐值得补的对照。模块删除、匹配替代、敏感性和外部验证各自说明目的；不会默认列出所有模块组合。

### 已有结果，想写成文章

~~~text
使用 $conference-helper。
我们已经有方法、结果表和图，如何把这些结果整理成一篇文章？
材料：[文件路径或粘贴内容]。
请给推荐的文章主线、论断与图表对应、章节安排，以及一段基于已有结果的示范文字。
保留负结果，证据缺口单独列出来。
~~~

先决定每项证据回答什么问题，再安排图表和章节。只写已有材料支持的结论，不从点估计补造显著性、机制证据或未做实验。

## 我们怎样推进研究

**具体问题 → 设计理由与假设 → 证据和竞争解释 → 最小下一步或文章交付。**

每轮只展开当前任务所需的部分。已有模型时沿用设计主线，已有结果时直接组织论证；文献检索为当前研究提供依据。默认在对话中交付，需要保存文件或可视化时再指定形式。

[三个完整教学案例](skills/conference-helper/examples/research-workflow-cases.md) · [消融计划模板](skills/conference-helper/assets/ablation-plan.md) · [可运行结果分析 Demo](examples/tiny-shapes/README.md) · [证据到写作示例](skills/conference-helper/examples/evidence-to-writing.md)


## 验证与文档

[验证记录](docs/TEST_REPORT.md) · [GitHub Actions](https://github.com/OneMore1/conference_helper/actions) · [用户手册](docs/USER_GUIDE.zh-CN.md) · [进阶命令](docs/QUICKSTART.zh-CN.md) · [维护与发布](docs/PUBLISHING.zh-CN.md)

软件检查与合成任务检查不替代真实科研验证。科学判断、引用与最终稿件需结合实际材料核对，投稿规则按会议当年要求确认。

[MIT License](LICENSE) · [BibTeX](CITATION.bib) · [Skill 入口](skills/conference-helper/SKILL.md)
