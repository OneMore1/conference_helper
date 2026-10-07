# 记录字段与离线检查器

本页用于已启用的持久化工作区；临时任务直接使用实际材料和来源定位，不要求填写这些字段。只读请求下仅检查已有记录。

## 项目
stage：ideation / design / writing / review / submission / rebuttal。
contribution_type：method / diagnostic / empirical / theory / dataset / systems。
novelty_assessment.status：not_assessed / insufficient_search / overlap_found / differentiated / needs_revision。
选题中的未知保持 not_assessed 或 insufficient_search。只有 differentiated 才要求最近邻正文读取记录、具体差异和本地 search_log。
方向未经作者确认时提示警告；不阻止正常讨论、草稿或局部改稿。

## 会议规则条目
以下只是字段示范，不是任何会议的实际规则：
```json
{
  "official_sources": [{
    "url": "https://OFFICIAL-DOMAIN/author-guidelines",
    "location_detail": "明确的年份、track、规则小节",
    "checked_on": "YYYY-MM-DD"
  }],
  "deadlines": [{
    "name": "当前阶段适用的截止时间",
    "datetime": "YYYY-MM-DDTHH:MM:SS-12:00",
    "original_text": "官网原始时间表述（示例 UTC 偏移不得照搬）",
    "source_url": "https://OFFICIAL-DOMAIN/author-guidelines"
  }],
  "prepared_artifacts": [{"path": "artifacts/main.pdf", "sha256": "实际文件的 SHA-256"}]
}
```
checks 的 status 可为 pass / fail / unknown / not_applicable。最后一种仍需说明不适用的具体依据。
正式 preflight 要求所有检查有 detail 和 evidence；网址必须与 official_sources 对应（纯内部检查可为空）。
manual_preflight_completed 只是操作者的记录，程序不能证明操作者真的检查过。

## 当天复核政策
submission 检查器要求 venue.checked_on 及 official_sources.checked_on 等于运行日期。
这是本包为最终打包采取的保守工作流默认值，不是任何会议规定。
`--as-of YYYY-MM-DD` 供明确指定当地核查日期或历史回归测试；不能伪造过去日期来宣称当前已复核。
程序检查时间格式及 UTC 偏移，提示已过日期，但不验证网站、更不保证平台仍开放。

## 文件边界
本地结果和待交付文件使用项目根目录内的相对路径。
已经登记的 sha256 会被复算比较；submission 阶段要求本地证据和交付文件都有哈希。
本包没有 PDF 渲染器、LaTeX 编译器、文献数据库连接器或统计分析引擎；需要宿主实际提供。

## 已确认版本比较
可运行：
`python scripts/workflow.py check PROJECT --stage review --baseline PROJECT/author-approved-project.json`
比较研究问题、资源约束、核心论断和可证伪计划。改变这些内容是允许的；已有明确作者决定时沿用，只对超出授权的改变确认，并更新受影响审查。
程序只提示差异，不会自动覆盖确认版本。局部文字修订不要求反复重选题。

## 状态与证据记录
project_state.json 是新的阶段权威记录，project.stage 仅为兼容字段。
参见 state-schema.md。来源账本记录来源与论断；阶段记录用于项目进度，两者用途不同。
