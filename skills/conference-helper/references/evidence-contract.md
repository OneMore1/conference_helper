# 证据契约：项目事实、研究假设与写作分离

以下文件和字段用于已启用的持久化工作区；临时或只读任务在交付中保留所需来源、论断边界和未决问题，不要求创建或更新 JSON。
project.json 存放用户问题、贡献类型、范围、预算和作者决定；project_state.json 是阶段记录的唯一权威文件，project.stage 仅为兼容字段。
evidence_ledger.json 存放 sources 与 claims。来源可以是公开论文、本地结果文件或作者在当前材料中明确确认的事实。
作者确认可以作为来源；不要因为工具没有原始数据就抹掉已有结果，也不要声称进行了独立复算。

## source 字段
source_id：项目内唯一标识；重复 ID 无法唯一定位，检查器会拒绝。
kind：public_paper / local_result / author_statement。
locator：URL、本地相对路径，或明确的作者陈述记录位置。
location_detail：节、页、表、图、行或具体陈述定位。
verification：unread / read / author_confirmed；这是操作记录，不是科学真值。
checked_on：YYYY-MM-DD。
sha256：本地结果文件的内容哈希，定稿记录；URL 不以这个字段假装已核验内容。

## claim 字段
claim_id、text、claim_type（hypothesis / empirical / literature / theoretical / method）。
use_in_manuscript（planned / background / method / reported_result）。
status（proposed / supported / author_confirmed）、evidence_ids、scope。
数值、统计单位、样本、切分、分析版本等放在 scope 中，必要时补字段，不依赖自然语言自动猜测。

reported_result 不得是 hypothesis 或 proposed，并且必须有已读取/作者确认的来源记录。
提出但尚未证明的定理不能标 supported；已有证明的 theoretical claim 可以作为结果，并定位证明。
观察数据与理论证明的类型不能混写。检索不足不等于结果无效，结果缺失也不等于科学否定。

## 写作与审查的分工
正文只使用与证据匹配的论断强度；修改日志承载事实冲突、缺失字段和编辑建议。
脚本检查 ID、状态、文件存在性、已登记哈希与人工确认记录；本地 source 或 artifact 变化会使关联阶段及下游需要刷新。不判断引用是否真的支持论断，也不验证统计正确性。
沿用作者明确提出或已确认的核心论断、预算和可证伪计划；拟作出超出既有授权的改变时再取得确认。启用持久化记录且允许写入时，可保存 author-approved-project.json 用于版本对照。

具体状态枚举与会议记录字段见 record-formats.md。
