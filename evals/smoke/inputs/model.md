# Synthetic model input
This is a teaching fixture, not real research.
模型 M 使用固定空间邻接先验 S 引导特征混合，再接时间模块 T 和线性读出。作者想支持空间结构本身有用，收益不是仅由更多参数造成。
只有单次 AUC：完整模型 0.80，另一种较小架构的基线 0.78。没有容量匹配、先验替代或不确定性结果。预算只允许追加两个对照组，本轮只规划，不运行。
