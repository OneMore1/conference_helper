# 进阶命令

日常使用直接调用 `$conference-helper`；这些命令用于安装和可选的本地项目记录。

## 安装

```bash
python tools/install_skill.py --project /path/to/project
python tools/install_skill.py --project /path/to/project --backup-existing
```

也支持 `--user` 安装到用户技能目录，或 `--destination` 指定以 `conference-helper` 结尾的完整路径。安装器拒绝默认覆盖，升级备份放在扫描目录之外。Windows 从较短的源码入口运行，并把研究目录作为参数传入。

## 记录研究进度

短任务无需初始化。希望跨会话维护状态时：

```bash
python skills/conference-helper/scripts/workflow.py init /path/to/project --project-id my-paper
python skills/conference-helper/scripts/workflow.py status /path/to/project
python skills/conference-helper/scripts/workflow.py record /path/to/project --input /path/to/state-draft.json --expected-revision 0
python skills/conference-helper/scripts/workflow.py check /path/to/project --stage design
```

状态草稿由 agent 依据材料形成，用户不必手填。提交要求当前 revision 匹配；检查只验证结构与已登记来源，不验证科学结论。

阶段记录位于 project_state.json，论断与来源位于 evidence_ledger.json。章节 scope 区分 full_paper 与 section；来源变化只刷新受影响的判断。普通 Windows 深路径由工具处理，但 Python 脚本入口和宿主发现仍受各自限制。

## 帮助与验证

```bash
python tools/install_skill.py --help
python skills/conference-helper/scripts/workflow.py --help
python tools/run_checks.py
python tools/demo.py
```

[用户手册](USER_GUIDE.zh-CN.md) · [状态格式](../skills/conference-helper/references/state-schema.md) · [验证记录](TEST_REPORT.md)
