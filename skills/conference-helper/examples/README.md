# 合成示例

| 示例 | 用途 |
|---|---|
| [三个研究入口](research-workflow-cases.md) | fMRI 方向、模型消融和结果成文的合成教学案例 |
| [问题到实验计划](problem-to-plan.md) | 宽泛方向、问题卡、构思卡与最小验证计划的衔接 |
| [证据到论文论证](evidence-to-writing.md) | 原稿、论断核对、Introduction/Results 修订与修改理由 |

这些案例为人工编写的教学材料；未执行研究，不作为实际 agent 效果评测，也不要求每次任务加载。

## 结构化路由夹具
partial-results-with-draft.state.json 描述“已有稿件、部分实验完成但未分析”。
它不是用户任何真实项目的判断，不包含真实科研数据。
auto 应推荐 analysis，同时 observed_stage 为 writing；显式 requested=writing 则保留写作任务。
不要将示例覆盖真实 project_state.json。
