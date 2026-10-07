# 维护与发布

项目仓库：[OneMore1/conference_helper](https://github.com/OneMore1/conference_helper)。技能目录：`skills/conference-helper/`。原创材料为 MIT，来源归纳保留相应 MIT / CC BY 4.0 署名。

## 验证

```bash
python tools/run_checks.py
python tools/demo.py
python tools/demo_case.py --output ../conference-helper-demo
```

测试生成的临时工作区位于仓库外。规则变更应另做实际任务调用，保存输入、输出和检查范围。示例教学文字不计作实际 agent 测试。

## 生成安装包

先审阅并明确暂存要发布的文件，确认不含私人稿件、被试信息、数据或凭据，再运行：

```bash
python tools/update_manifest.py
git add PACKAGE-MANIFEST.json
git diff --cached --check
python tools/build_release.py --output ../conference-helper-release
```

清单记录暂存文件的哈希与字节，工作树必须与暂存内容相同。构建输出目录须在源码仓库之外且不存在；输出为完整源码 ZIP、独立 Skill ZIP 和 SHA256SUMS.txt。

从实际 ZIP 解压检查安装、CLI 初始化、拒绝覆盖、升级备份及许可保留。提交推送后核对对应 SHA 的 CI；打标签和上传 Release 资产时使用该已验证提交及安装包。

## 发布边界

Git 提交、创建 Release、改变可见性和运行科研任务分别需要相应授权。不要 force push 或覆盖已有发布文件；纠正已发布包应使用新版本。工作区、测试输出与凭据存放在源码之外。公开前审阅完整待发布内容，不只依赖忽略规则。

[用户手册](USER_GUIDE.zh-CN.md) · [进阶命令](QUICKSTART.zh-CN.md) · [验证记录](TEST_REPORT.md)
