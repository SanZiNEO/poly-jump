# PolyJump AI Research

本目录用于 **AI 研究 / 平台能力验证**，与游戏运行时（`backend/`）解耦。

## 目标

第一阶段不做复杂训练，只做：
- 给 AI 一个明确目标：把本方棋子搬到对方目标区。
- 关闭计分，先比较“谁先把棋子搬完”的效率。
- 用 B 模型 2 人局作为公平基准（固定 12 向、偶子晶格、最接近传统跳棋）。
- 验证 PolyJump 的 `GameEnv` 接口是否足以承载不同 AI 的研究。
- 所有对局记录、指标、曲线统一按时间戳归档，方便后续复盘和对比。

## 目录结构

```text
ai_research/
├── agents/                      # 每个 AI 独立一个子目录
│   ├── base.py                  # Agent 基类 + 公共工具
│   ├── random_ai/               # 随机 AI
│   ├── manhattan_ai/            # 曼哈顿距离贪心
│   ├── euclidean_ai/            # 欧氏距离贪心
│   ├── chebyshev_ai/            # 切比雪夫距离贪心
│   └── graph_bfs_ai/            # 图距离 BFS 贪心
├── metrics.py                   # 指标计算与汇总
├── runner.py                    # 批量评测入口
└── runs/                        # 实验结果（按时间戳归档，已 gitignore）
```

## 运行

在项目根目录，使用项目虚拟环境：

```powershell
.poly_jump\Scripts\python.exe -m ai_research.runner --games 10 --radius 6
```

常用参数：

| 参数 | 默认 | 说明 |
|---|---|---|
| `--agents` | `random,manhattan,euclidean,chebyshev,graph_bfs` | 参与评测的 AI |
| `--games` | `10` | 每对组合各跑几局 |
| `--radius` | `6` | B 模型半径 R |
| `--max-steps` | `2000` | 单局最大步数 |
| `--seed` | `42` | 随机种子 |
| `--out` | `ai_research/runs` | 输出根目录 |

示例：只跑曼哈顿和图距离，每对 20 局：

```powershell
.poly_jump\Scripts\python.exe -m ai_research.runner --agents manhattan,graph_bfs --games 20
```

## 输出说明

每次运行生成一个带时间戳的目录：

```text
runs/20260708_153000/
├── experiment.json       本次实验配置快照
├── matches/              每局完整对局记录
├── metrics.json          聚合指标
├── curves.csv            基础性能表
├── summary.md            人类可读总结
└── learning_curves/      预留给学习曲线/训练曲线
```

`summary.md` 中的关键指标：

- **胜率**：谁更常赢。
- **平均步数**：谁更快完成目标。
- **平均终局进目标子数**：效率的直接体现。
- **平均离开目标区次数**：越小越好，对应“AI 进了目标区又出来”的问题。
- **平均穿过目标区次数**：经过了目标区但没停下来的次数。

## 后续

- 第二阶段：加 Minimax / MCTS / UCT，输出“搜索预算 vs 胜率”的性能曲线。
- 第三阶段：接 RL / AlphaZero，输出真正的训练曲线。
- 所有结果都按 `runs/<时间戳>/` 归档，可随时回溯和对比。
