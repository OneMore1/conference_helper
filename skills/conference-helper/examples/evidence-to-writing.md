# 教学示例：从原稿与证据到 Introduction / Results

本例的项目、方法、数字和稿件全部为合成教学材料。没有执行研究，也不是 agent 效果评测。
它示范“先核对论断，再改写论证”的过程；不要将本例数字、结论或句子当作真实研究证据。

## 1. 本轮任务与可用材料

用户请求：只重写 Introduction 和 Results，保留已确定的噪声增强方向与给出的结果；其他章节不改，不补实验，不创建状态文件。

项目说明：比较相同图形分类器的 Baseline 与 NoiseAug。NoiseAug 只在训练阶段增加输入噪声。
两者使用相同固定划分、训练预算和验证集 checkpoint 选择规则。
评价包括 clean、noise、shift 三个条件，共享同一组基础测试图像。每种方法提供三个配对 seed 条目。
当前材料没有文献检索、机制实验、逐样本预测或推断统计。

合成原始表（单位为准确率百分比）：

| 条件 | Baseline 的 seed 1 / 2 / 3 | NoiseAug 的 seed 1 / 2 / 3 |
|---|---|---|
| clean | 82 / 83 / 84 | 83 / 84 / 85 |
| noise | 69 / 70 / 71 | 73 / 74 / 75 |
| shift | 63 / 64 / 65 | 61 / 63 / 65 |

统计口径：按条件汇总 seed 均值与样本标准差；方法差值先按同一 seed 配对再求均值。
这些是固定测试集上的重复条目，不能当作三个独立数据集。

## 2. 原稿

**Introduction 原稿（故意保留待核对的论断）：**

> Existing classifiers fail to handle real-world variation. Our noise augmentation solves this limitation by learning invariant representations. We establish a new state of the art and demonstrate robust improvements under every evaluated condition.

**Results 原稿：**

> NoiseAug achieved 74% accuracy under noise, compared with 70% for Baseline, a 4% improvement. All conditions improved significantly. These results prove that the model learns invariant features that generalize to unseen distributions.

数字 74 与 70 可以在表中找到；“4%”“所有条件”“显著”“机制”和“未见分布”的含义仍需分别核对。

## 3. 论断—证据—修改决定

| 位置与论断 | 给出的依据 | 判断与修改 |
|---|---|---|
| 引言：所有现有分类器都失败 | 只有一个内部基线，没有最近邻文献 | 改为具体研究问题；不捏造整个领域的缺陷 |
| 引言：SOTA | 没有公开基准或文献比较 | 删除该认证，不补写虚构引用 |
| 结果：noise 提高 4% | 74 − 70 = 4 | 单位应为 **4 个百分点**；相对提升是另一口径，不能混写 |
| 结果：所有条件均改善 | clean +1、noise +4、shift −1 个百分点 | 逐条件报告；保留 shift 的下降 |
| 结果：显著改善 | 没有推断检验与相应独立单位证据 | 只描述均值变化，不生成 p 值 |
| 引言/结果：不变表征机制已证明 | 只有准确率，没有可区分机制的证据 | 去掉机制证明；可作为后续待验证解释 |
| 结果：可泛化到未见分布 | 当前只有固定测试集的三个条件 | 将结论限定为当前评价条件 |

描述性核算：

| 条件 | Baseline 均值 ± SD (%) | NoiseAug 均值 ± SD (%) | 配对差值均值（百分点） |
|---|---:|---:|---:|
| clean | 83.00 ± 1.00 | 84.00 ± 1.00 | +1.00 |
| noise | 70.00 ± 1.00 | 74.00 ± 1.00 | +4.00 |
| shift | 64.00 ± 1.00 | 63.00 ± 2.00 | −1.00 |

例如 shift 的配对差值为 −2、−1、0，均值为 −1。SD 描述三个 seed 条目的变异，不提供跨数据集的推断结论。

## 4. 改写后的论证

**Introduction 修订稿（教学文本）：**

> Training-time noise augmentation may affect performance differently across evaluation conditions. In this teaching example, we ask whether adding noise to the training inputs improves classification under test-time noise, and how it affects clean and shifted inputs. We compare an unaugmented classifier with a noise-augmented variant using the same architecture, data split, training budget, and checkpoint-selection rule. Evaluation across three fixed conditions allows us to describe where the augmentation helps and where its benefit is limited.

改写理由：先给具体问题与比较操作；贡献落在能够观察的条件差异上；不承诺新颖性、普遍鲁棒性或机制发现。
真实论文中应使用作者实际问题、方法与来源；本例的 teaching example 标注仅属于教学材料。

**Results 修订稿（教学文本）：**

> In the illustrative results, NoiseAug increased mean accuracy under noise from 70% to 74%, a gain of 4 percentage points. Mean accuracy also increased from 83% to 84% for clean inputs, but decreased from 64% to 63% under the shift condition. These values describe three paired seed entries on a fixed test set. They support a condition-specific descriptive benefit under noise; they do not establish statistical significance, invariant representations, or generalization beyond the evaluated conditions.

改写理由：先报告主要观察，再报告边界和负结果。统计口径随数值给出，不把准确率变化升级成机制结论。
这里对推断范围的说明是科学解释；工具没拿到文件、编辑过程未完成等流程注释应放在备忘录中。

## 5. 独立编辑备忘录

- 已完成指定两节的论证改写，方法方向与表格数字保留；没有修改其他章节或输入文件。
- “全球领先”和“现有方法都失败”缺少来源，已从正文移除；若作者以后要求保留，需取得相应文献或基准证据。
- 未做新的显著性检验或机制分析，未声称完成实验。
- 推荐下一步：在真实项目中核对表格与运行版本，再确认作者接受当前限定范围。若当前写作目标就是描述这些条件差异，无需为了文字改稿自动增加实验。
- 停止条件：本轮修订中的结果数字能定位、正负方向保留、单位一致，Introduction 和 Results 不再将当前性能表写成普遍或机制证明；其他章节的问题只记入待办。

## 6. 可复制的请求

```text
使用 $conference-helper。
先读我的原稿、结果表及比较设定，只改 Introduction 和 Results。
先给简短的论断—证据对应，再交付修订稿和独立编辑备忘录。
保留研究方向与已确认的数字；来源不足时限制论断，不补造论文或实验。
不要改其他章节、启动实验或创建 JSON 工作区。
```

验收重点是事实与论证关系，不要求逐字复制以上措辞。实际任务只加载有关材料，不以完成本示例所有栏目作为局部改稿前置条件。
