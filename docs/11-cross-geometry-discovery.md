# PolyJump 跨几何路径策略差异初步发现

## 结论摘要

在相同算法、相同搜索预算下，**棋盘几何结构会系统性改变 AI 的路径选择策略**。

具体表现：

| 模型 | MCTS 行为 |
|---|---|
| A（9×9×9，6+12+8 向） | 偏向选择更短路径 |
| B（R=6，12 向） | 偏向选择长连跳，detour 更高 |
| C（R=6，20 向） | 偏向选择长连跳，detour 更高 |
| D（金字塔，14 向） | 偏向选择更短路径 |

这说明 PolyJump 可以作为**可配置的空间规划 / 多几何博弈研究环境**，而不仅仅是一个 3D 跳棋游戏。

---

## 实验目的

验证：

1. PolyJump 是否能承载 AI 行为对比实验；
2. 不同几何模型是否会让同一 AI 产生可观测的策略差异；
3. 传统“胜率/步数”之外，路径指标是否能揭示更多差异。

---

## 实验设置

| 项 | 设置 |
|---|---|
| 模型 | A 9³、B R=6、C R=6、D ep_side=5 |
| AI | random、euclidean、chebyshev、graph_bfs、mcts |
| 局数 | 每个 AI 每个模型 8 局（先后手各 4 局） |
| 每局最大 action | 6 |
| MCTS 模拟次数 | 5 |
| 随机种子 | 固定种子（42 开启） |
| 计分 | 关闭 |
| 吃子 | 关闭 |

---

## 结果

| 模型 | agent | 平均 steps | 平均 path | 平均 straight | 平均 detour |
|---|---|---|---|---|---|
| A | random | 3.00 | 4.59 | 4.59 | 1.00 |
| A | euclidean | 3.00 | 10.39 | 10.39 | 1.00 |
| A | chebyshev | 3.00 | 10.39 | 10.39 | 1.00 |
| A | graph_bfs | 3.00 | 10.39 | 10.39 | 1.00 |
| A | mcts | 3.00 | **5.20** | 5.20 | 1.00 |
| B | random | 3.00 | 5.48 | 5.48 | 1.00 |
| B | euclidean | 3.00 | 8.49 | 8.49 | 1.00 |
| B | chebyshev | 3.25 | 9.19 | 9.00 | 1.02 |
| B | graph_bfs | 3.25 | 9.19 | 9.00 | 1.02 |
| B | mcts | 5.00 | **14.14** | 10.83 | **1.31** |
| C | random | 3.00 | 5.13 | 5.13 | 1.00 |
| C | euclidean | 3.12 | 8.84 | 8.63 | 1.02 |
| C | chebyshev | 3.00 | 8.56 | 8.56 | 1.00 |
| C | graph_bfs | 3.00 | 8.56 | 8.56 | 1.00 |
| C | mcts | 4.00 | **11.26** | 8.33 | **1.26** |
| D | random | 3.00 | 5.05 | 5.05 | 1.00 |
| D | euclidean | 3.38 | 9.86 | 8.92 | 1.09 |
| D | chebyshev | 3.00 | 8.02 | 8.02 | 1.00 |
| D | graph_bfs | 3.00 | 8.02 | 8.02 | 1.00 |
| D | mcts | 3.00 | **5.20** | 5.20 | 1.00 |

---

## 关键观察

### A / D：MCTS 更倾向于短路径

- A：MCTS path=5.20，三个距离启发式均为 10.39
- D：MCTS path=5.20，启发式约 8.0
- detour 均为 1.00

### B / C：MCTS 更倾向于长链

- B：MCTS steps=5，detour=1.31
- C：MCTS steps=4，detour=1.26
- 距离启发式 detour 约 1.01

这说明：

> 同样的 MCTS 算法，放到不同几何结构里，会表现出完全不同的路径选择偏好。

---

## 稳定性

- A：MCTS 多局结果稳定，path 均为 5.20，std=0
- B：MCTS 多局结果稳定，detour=1.31，std=0
- C：MCTS 平均 detour=1.26，std=0.26
- D：MCTS 多局结果稳定，path 均为 5.20，std=0

结果为系统性差异，不是偶然波动。

---

## 为什么这能证明 PolyJump 有价值

传统棋类环境主要观察：

- 胜率
- 步数
- 搜索深度

PolyJump 还可以观察：

- action 数
- step 数
- straight_distance
- path_distance
- detour
- step_per_action

并且：

> 同一 AI 在不同几何模型上的路径选择策略会发生系统性变化。

这意味着 PolyJump 是一个可以研究：

- 空间路径规划
- 非直觉最短路径
- 跨几何泛化
- 多玩家策略
- 变长路径动作决策

的研究环境。

---

## 复现

```powershell
.poly_jump\Scripts\python.exe -m ai_research.cross_model_finding --games 4 --max-actions 6 --mcts-simulations 5 --seeds 42
```

---

## 局限

- 本实验是**初步发现**，不是严格学术研究。
- 每局限制 6 个 action，没有跑到终局，因此没有胜率结论。
- MCTS 使用 5 次模拟，属于低预算 baseline。
- 后续若要更硬，可增加局数、提高 MCTS 预算、跑到终局、加入置信区间和统计检验。
