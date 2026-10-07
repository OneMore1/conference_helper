# Demo：有初稿和结果，接下来怎么做？

这是虚构的 TinyShapes 图形分类项目。所有方法设定、数据量、seed 和结果数字均为手工构造的教学材料，没有训练模型或产生真实科研结果。

这个用例展示三件事：已有初稿仍可能需要先解释结果；用户只要求改 Methods 时继续完成局部任务；证据缺口可以通过收缩论断处理。

## 先看输入与交付

| 输入 | 应获得的交付 |
|---|---|
| [项目说明](materials/brief.md)、[实验设定](materials/protocol.md)、[18 行结果](materials/results.csv)、[短稿](materials/draft.md) | 带来源的描述性汇总和论断边界 |
| 只改 Methods 的明确要求 | 英文 Methods 修订稿，其他问题进入独立备忘录 |
| 不追加训练，确定下一步 | 最小修改计划与可接续的短交接记录 |

## 在本地运行

在仓库根目录执行，将示例复制到仓库之外的一个新目录，并重算结果表：

```bash
python tools/demo_case.py --output ../conference-helper-demo
python tools/install_skill.py --project ../conference-helper-demo
```

Windows 示例：

```powershell
python tools/demo_case.py --output "C:\Research\conference-helper-demo"
python tools/install_skill.py --project "C:\Research\conference-helper-demo"
```

输出目录已存在时命令会拒绝覆盖；再次试用请换一个新目录。
在 Codex 中打开新目录，按 [三轮提示词](prompts.md) 逐轮提问。
第一次只提供 `materials/`，完成后再对照 `reference/`。结果措辞可不同，验收要点应一致。

`tools/demo_case.py` 只复制合成材料、核对行与配对关系、重算均值/样本标准差和差值。
它不调用语言模型，也不替 agent 判断阶段。`reference/` 是人工编写的示例交付，不是运行日志或真实科研质量评测。

## 数值自检

| 条件 | Baseline 平均准确率 | Augmented 平均准确率 | 配对差值 |
|---|---:|---:|---:|
| clean | 83.00% | 84.00% | +1.00 个百分点 |
| noise | 70.00% | 74.00% | +4.00 个百分点 |
| shift | 64.00% | 63.00% | −1.00 个百分点 |

每格由三个示例 seed 构成。同一测试集上的重复 seed 不能当作三个独立数据集。
仅凭这些演示数据不能写“所有条件均提升”“统计显著”“达到 SOTA”或“机制已证明”。

## 对照交付

1. [分析示例](reference/01-analysis.md)
2. [局部改稿与编辑备忘录](reference/02-methods.md)
3. [最小动作与交接](reference/03-next-step.md)

旧的 `python tools/demo.py` 仍用于三个结构化状态路由自检；它与本案例用途不同。
