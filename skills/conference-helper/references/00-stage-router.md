# 阶段诊断与任务路由

## 输入优先级
当前明确任务 > 作者已确认的范围/决策 > 最新有定位的项目材料 > 旧状态记录 > 无依据推测。
旧状态不是事实替代品；目录存在不证明完成，材料未挂载也不证明作者没有完成。
先读取与任务有关材料，抽取小型 inventory，再由 agent 填结构化 assessment。

## 维度，而非一个百分比
research_question：问题及边界是否清楚。
literature_grounding：最近邻和具体不足是否有来源。
concept：方案、机制、可检验预测是否具体。
experiment_plan：对照、划分、指标、统计单位、资源是否明确。
experiments：实际计算/采集是否完成；有初步结果可记 in_progress。
result_analysis：结果整理和解释是否完成。
evidence_gaps：核心论断的剩余缺口是否审计完成。
manuscript：本轮目标范围的稿件是否完成；scope 使用 full_paper / section，具体章节写在 note。
internal_review：是否完成科学和一致性检查。
venue_compliance：是否核查对应会议/年份/track/阶段。
submission_receipt：是否真的取得回执。
理论/数据/系统论文可以有不适用维度，但必须写明对应的替代证据。

## 默认规则
信息太少且没有明确问题 → intake，先读材料，再提出关键问题。
方向宽泛但可界定问题 → topic。
已有问题、没有明确可检验方案 → ideation。
方案具体、验证方案未定 → design。
设计已定、未获得结果 → execution。
已有初步或完整结果但未充分解释 → analysis（即使稿件已存在）。
分析已有、关键证据缺口未解决 → supplement；先诊断缺口，不自动跑新实验。
证据足以支持当前限定论断 → writing。
稿件已成形 → review；已完成科学审阅则 submission。
有真实审稿意见且用户要回复 → rebuttal。

这是推荐 next_action，不是对整个项目贴唯一标签。
根据最成熟的有依据维度报告 observed_stage；用科学依赖报告 recommended_stage；
用户指定环节时 active_stage 尊重该任务，另列 blockers。
例如“稿件已有，只有缺失的对照未完成，用户只让改 Methods”：
observed=writing；recommended=supplement；active=writing；不把它判为投稿完成。

## 最小阶段卡
首次诊断或证据变化时使用；局部润色和连续追问按 [交互规则](interaction.md) 缩短展示。
主要阶段：结果分析（初步结果已存在）。
本轮执行：analysis。
依据：结果表版本、日志、作者确认的位置。
关键缺口：尚未区分替代解释，而非简单“实验数量不够”。
可并行：已确认 Methods 的文字整理。
本轮交付：结果解释表 + 最小必要补充建议。

## 变化与回退
method / hypothesis 变化 → 最近邻、设计、分析、论断、稿件检查按依赖失效。
split / sample / preprocessing 变化 → 受影响结果及相关论断失效。
仅拼写或标题变化 → 不让整个研究重新开始。
旧实验结果保留，不伪造它们已经验证新版方法。
有持久化工作区时，每条依赖失效记录 reason、affected_fields 和来源定位；程序按这些记录降低就绪状态。临时或只读任务在交付中说明受影响部分及依据即可。

## 多分支
每个 workstream 独立 assessment、artifacts、gaps、invalidations 和 requested_stage。
当前任务不明确指向哪个分支且会改变动作时，再问一次；不能合并不相干论文的进度。

## 确认策略
例行读材料、总结、已有授权的修改与执行无需每阶段再问；只读、局部修改和预算边界持续有效。
作者明确提出或已经确认的研究问题、分析方法和实验选择按其要求执行，并记录必要解释边界。建议改变主线、主要分析或扩大预算时，先判断是否超出已有授权；只对超出的部分取得确认。
“补实验”本身不能确定高成本作业的范围与预算；若这些条件已明确授权，不再重复确认。实际投稿等外部动作同样沿用已有明确授权。

## 状态与范围约定
manuscript 和 internal_review 支持 scope: full_paper / section。局部章节完成或审阅不等于整篇稿件完成。
旧状态缺少 scope 时按 full_paper 兼容，迁移时由 agent 核对范围，不能仅凭旧记录认定定稿。
状态里的 source:ID 必须能够在 evidence_ledger.json 中唯一定位。本地 source 或 artifact 文件缺失、已登记哈希不符时，其关联维度及下游需要刷新；无需为同一来源重复登记 artifact。
研究问题或最近邻材料失效时先刷新对应部分；用户指定本轮任务仍保持不变。
