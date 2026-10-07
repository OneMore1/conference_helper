# 第二轮参考交付：仅修改 Methods

这是一份人工编写的参考回复。下面的英文用于练习，全部方法设定来自合成案例。

本轮只整理 Methods，依据 [protocol.md](../materials/protocol.md) P1–P3；其他章节的问题记在备忘录中。

## 修订后的 Methods 概要

In this synthetic teaching example, we compare a baseline classifier with an augmented variant on a three-class shape classification task. Both variants use the same architecture, comprising two convolutional layers and a linear classification head, with a fixed split of 600 training, 150 validation, and 150 test images. The augmented variant adds zero-mean Gaussian noise with a standard deviation of 0.1 to training inputs scaled to [0, 1], followed by clipping to this range. Both variants use Adam with a learning rate of 0.001, a batch size of 32, and 20 training epochs. For each variant and seed, the checkpoint with the highest clean-validation accuracy is selected. Clean, noise, and shift conditions are evaluated using the same 150 base test images; the test data are not used for checkpoint selection. We summarize three paired seed entries (1, 2, and 3) using their mean accuracy and sample standard deviation. All values in the accompanying table are manually constructed for workflow demonstration and are not empirical measurements.

## 独立编辑备忘录

- 根据 protocol P2 和 results.csv，将原稿的 five seeds 修正为 three seeds；没有改结果表。
- 原稿未说明 “best model” 的依据，现补为 clean-validation accuracy。
- 卷积通道数、卷积核大小、测试噪声强度和 shift 幅度尚无来源；未补造。P4 已明确这些缺口，因此这是方法概要，不是完整复现规格。
- Abstract 和 Results 的过度概括仍待处理，本轮没有替换它们。
- Methods 局部交付完成；全文审阅、创新性核对及投稿准备仍未完成。这个临时任务没有创建状态 JSON。
