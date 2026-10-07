# 状态记录与脚本边界
仅在启用持久化工作区时使用本页；临时任务不要求状态文件，只读任务不更新已有状态。
schema_version="0.2"；revision 为从 0 开始的整数；project_id 不随状态更新改变。
active_workstream 指向 workstreams 中的一个分支。
requested_stage 是用户的本轮显式任务或 auto；最新原话放 latest_request。
每个 assessment 保留 status、evidence、note、assessed_by、confidence。
confidence 是基于所读材料的定性判断，不是经过校准的概率。
artifacts 记录 id、工作区内相对 path 和可选 sha256。它本身不赋予 complete 状态。
source:ID 引用 evidence_ledger.json 中唯一的 source_id；未知或重复 ID 会被拒绝。
状态诊断检查 artifact 及所引用 local_result source 的本地文件：缺失或已登记 SHA-256 不符时，将关联维度及下游标为需要刷新。无需将同一 source 再登记为 artifact；未登记哈希时不能据此检测内容变化。
URL 与作者陈述不由离线脚本重新核验；来源正文是否支持判断、记录是否真实仍须 agent/人工核对。完整账本字段由 `workflow.py check` 检查。
gaps 记录 id、reason、priority(blocking/supportive/optional)、status(open/resolved/deferred)。
blocking 缺口即使 deferred 仍是核心论断的未解决事项；减小论断后须说明为什么该缺口不再阻塞。
invalidations 记录 reason、affected_fields、status(open/resolved)；改变输入时先记录，再重做受影响任务。
脚本根据依赖提示下游需要更新，但不会覆盖数据或自动重跑实验。
状态文件缺失或不可读时先恢复材料；不要推断科研从未开展。

## 状态与范围约定
manuscript 和 internal_review 支持 scope: full_paper / section。局部章节完成或审阅不等于整篇稿件完成。
旧状态缺少 scope 时按 full_paper 兼容，迁移时由 agent 核对范围，不能仅凭旧记录认定定稿。
状态里的 source:ID 必须能够在 evidence_ledger.json 中唯一定位；文件变化检测不等于验证科学真伪。
研究问题或最近邻材料失效时先刷新对应部分；用户指定本轮任务仍保持不变。
