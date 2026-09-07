# PolyJump 跨几何路径指标数据记录

## 实验设置

| 项 | 设置 |
|---|---|
| 模型 | A 9³、B R=6、C R=6、D ep_side=5 |
| AI | random、euclidean、chebyshev、graph_bfs、mcts |
| 局数 | 每个 AI 每个模型 8 局（先后手各 4 局） |
| 每局最大 action | 6 |
| MCTS 模拟次数 | 5 |
| 随机种子 | 固定种子 |
| 计分 | 关闭 |
| 吃子 | 关闭 |

## 结果

| 模型 | agent | 平均 steps | 平均 path | 平均 straight | 平均 detour |
|---|---|---|---|---|---|
| A | random | 3.00 | 4.59 | 4.59 | 1.00 |
| A | euclidean | 3.00 | 10.39 | 10.39 | 1.00 |
| A | chebyshev | 3.00 | 10.39 | 10.39 | 1.00 |
| A | graph_bfs | 3.00 | 10.39 | 10.39 | 1.00 |
| A | mcts | 3.00 | 5.20 | 5.20 | 1.00 |
| B | random | 3.00 | 5.48 | 5.48 | 1.00 |
| B | euclidean | 3.00 | 8.49 | 8.49 | 1.00 |
| B | chebyshev | 3.25 | 9.19 | 9.00 | 1.02 |
| B | graph_bfs | 3.25 | 9.19 | 9.00 | 1.02 |
| B | mcts | 5.00 | 14.14 | 10.83 | 1.31 |
| C | random | 3.00 | 5.13 | 5.13 | 1.00 |
| C | euclidean | 3.12 | 8.84 | 8.63 | 1.02 |
| C | chebyshev | 3.00 | 8.56 | 8.56 | 1.00 |
| C | graph_bfs | 3.00 | 8.56 | 8.56 | 1.00 |
| C | mcts | 4.00 | 11.26 | 8.33 | 1.26 |
| D | random | 3.00 | 5.05 | 5.05 | 1.00 |
| D | euclidean | 3.38 | 9.86 | 8.92 | 1.09 |
| D | chebyshev | 3.00 | 8.02 | 8.02 | 1.00 |
| D | graph_bfs | 3.00 | 8.02 | 8.02 | 1.00 |
| D | mcts | 3.00 | 5.20 | 5.20 | 1.00 |

## 稳定性

- A：MCTS 多局 path 均为 5.20，std=0
- B：MCTS 多局 detour=1.31，std=0
- C：MCTS 平均 detour=1.26，std=0.26
- D：MCTS 多局 path 均为 5.20，std=0

## 复现

```powershell
.poly_jump\Scripts\python.exe -m ai_research.cross_model_finding --games 4 --max-actions 6 --mcts-simulations 5 --seeds 42
```

## 局限

- 本实验为小规模数据记录。
- 每局限制 6 个 action，未跑到终局。
- MCTS 使用 5 次模拟。
- 被测 AI 以随机 AI 作为对手，用于观察路径指标。
