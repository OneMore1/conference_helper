# 第三轮参考交付：最小动作与交接

以下是合成用例的计划示例，未执行稿件修改或新训练。

## 推荐下一步

在获得改写这些章节的任务后，收缩 [draft.md](../materials/draft.md) 的 Abstract 与 Results 三个陈述，使结论范围与当前表格一致。

| 位置 | 最小动作 | 停止条件 |
|---|---|---|
| Abstract：“every evaluated condition” | 改为逐条件描述，保留 shift 下降 | clean +1、noise +4、shift −1 个百分点均准确可定位 |
| Abstract：“broad robustness” | 将范围限定在当前合成设定 | 不外推到未知分布或真实数据 |
| Results：“invariant representations” | 删除已证明机制的断言，或明确作为待验证解释 | 不再把准确率变化当作机制证明 |

此项工作可用已有材料完成，不需要新训练。若以后选择保留广泛泛化或机制论断，应另行设计能区分解释的验证方案。

## 可复制的交接说明

```text
继续 TinyShapes 合成案例。方向已确定，无新训练预算。
材料：materials/brief.md、protocol.md、results.csv、draft.md。
已完成：18 行表格的描述性汇总；Methods 英文概要及编辑备忘录。
数值：clean +1、noise +4、shift −1 个百分点，均为 Augmented−Baseline。
未决：Abstract/Results 的过度概括；完整方法细节；真实文献与外部验证。
建议下一步：只修正 Abstract/Results 的论断范围，保留负结果。
所有材料与数值均为虚构教学内容，未开展实验、未建立持久化状态、未准备真实投稿。
```
