# 验证记录

版本：0.1.0。日期：2026-10-07。

| 验证 | 结果与范围 |
|---|---|
| 完整本地检查 | Windows / Python 3.12.14，106 项运行时与 49 项仓库检查通过，共 155 项 |
| 路由 Demo | 3 个合成状态示例通过 |
| Skill 入口 | quick_validate.py 校验通过，使用已有 Conda Python / UTF-8 |
| 实际任务调用 | 方向、消融、写作三项独立合成调用完成，保留输入与实际答复 |
| 名称与文档 | conference_helper 仓库、conference-helper Skill、包名及调用示例一致 |

[测试输出](TEST_OUTPUT.txt) · [实际任务检查](../evals/smoke/README.md) · [当前 GitHub Actions](https://github.com/OneMore1/conference_helper/actions)

复现命令：

~~~bash
python tools/run_checks.py
python tools/demo.py
~~~

运行时检查覆盖阶段与当前任务、来源变化、状态冲突、路径边界、安装备份与分发完整性。CI 配置为 Linux / Windows × Python 3.10 / 3.12；远端通过状态以具体提交的运行记录为准。

合成任务没有基线组或盲评分。文献与科学判断需要真实材料核查，以上记录不证明研究质量或录用率提高。实际包的安装与哈希记录随分发包提供。
