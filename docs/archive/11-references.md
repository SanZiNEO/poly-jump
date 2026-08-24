# PolyJump 参考项目与资料

本文档列出 PolyJump 设计过程中参考的项目、代码仓库和资料。  
实现者、合作者或评审者可以直接通过这些链接了解设计来源。

---

## 1. 三维围棋参考项目

PolyJump 的“三维棋盘”和“空间博弈”灵感来自以下项目。

| 项目 | 链接 | 参考点 |
|---|---|---|
| KataGomo 三维围棋分支 | https://github.com/hzyhhzy/KataGomo/tree/3d_go | 三维棋盘、三维坐标、三维跳/吃/气结构 |
| Lizzie3D 三维棋盘界面 | https://github.com/hzyhhzy/Lizzie3D | 3D 棋盘可视化、三维坐标输入、SGF 支持 |
| KataGomo 3D 围棋成品发布页 | https://github.com/hzyhhzy/KataGomo/releases/tag/3d_go_20260620 | 已训练好的 3D 围棋 AI 与配套资源 |
| KataGomo 主仓库 | https://github.com/hzyhhzy/KataGomo | KataGo 魔改框架，自博弈训练管线 |

对应 B 站视频主题：

> 《3D围棋：从围空游戏变成做眼破眼大赛》

---

## 2. 二维中国跳棋 / Sternhalma / Halma 参考项目

这些项目用于参考“二维跳棋”的规则、移动生成、连跳处理、AI 与训练框架。

### 2.1 规则 / 实现参考

| 项目 | 链接 | 参考点 |
|---|---|---|
| `henrychess/pygame-chinese-checkers` | https://github.com/henrychess/pygame-chinese-checkers | 中国跳棋规则清晰实现：相邻走、单跳、连跳 |
| `masarwy/SternhalmaEnv` | https://github.com/masarwy/SternhalmaEnv | PettingZoo 多智能体中国跳棋环境 |
| `masarwy/SternhalmaMARL` | https://github.com/masarwy/SternhalmaMARL | RLlib PPO/IPPO 训练脚手架 |
| `kenziyuliu/ChineseCheckersAgent` | https://github.com/kenziyuliu/ChineseCheckersAgent | MCTS + 自博弈强化学习 |
| `timjb/halma` | https://github.com/timjb/halma | Haskell 函数式中国跳棋实现 |
| `denvaar/sternhalma` | https://github.com/denvaar/sternhalma | Elixir 中国跳棋库 |
| `anchengjian/chinese_checkers` | https://github.com/anchengjian/chinese_checkers | React + Socket.io 联机中国跳棋 |
| `clysto/chinese-checkers` | https://github.com/clysto/chinese-checkers | C++ Alpha-Beta + MTD(f) 搜索 |
| `M-E-L-S/Halma` | https://github.com/M-E-L-S/Halma | Python + NNUE 中国跳棋智能体 |
| `a-leut/chinese_checkers_ai_mcts` | https://github.com/a-leut/chinese_checkers_ai_mcts | MCTS 中国跳棋 AI |
| `SVJayanthi/ChineseCheckersMCTS` | https://github.com/SVJayanthi/ChineseCheckersMCTS | MCTS 中国跳棋 AI |

### 2.2 规则说明资料

| 资料 | 链接 | 参考点 |
|---|---|---|
| Chinese Checkers（维基百科） | https://en.wikipedia.org/wiki/Chinese_checkers | 标准中国跳棋规则 |
| Halma（维基百科） | https://en.wikipedia.org/wiki/Halma | Halma 原始规则 |
| Draughts / International Checkers（维基百科） | https://en.wikipedia.org/wiki/Draughts | 国际跳棋吃子规则 |

---

## 3. B 模型几何参考

B 模型使用 FCC 点阵 / 菱形十二面体 / 12 向等步长移动。

| 资料 | 链接 | 参考点 |
|---|---|---|
| Rhombic dodecahedron（维基百科） | https://en.wikipedia.org/wiki/Rhombic_dodecahedron | FCC 的 Voronoi 胞 / 菱形十二面体 |
| Cubic crystal system（维基百科） | https://en.wikipedia.org/wiki/Cubic_crystal_system | FCC 面心立方晶格 |
| Face-centered cubic | https://en.wikipedia.org/wiki/Cubic_crystal_system#Bravais_lattices | 12 个最近邻方向 |

---

## 4. 训练 / RL 参考

| 项目 | 链接 | 参考点 |
|---|---|---|
| KataGo | https://github.com/lightvector/KataGo | 自博弈、MCTS、数据管线 |
| KataGomo | https://github.com/hzyhhzy/KataGomo | 将 KataGo 改造成多种棋类 |
| SternhalmaMARL | https://github.com/masarwy/SternhalmaMARL | IPPO 多智能体训练与评测 |

---

## 5. 阅读建议

如果你是实现者，建议按顺序阅读：

1. `01-rules-2d-checkers.md` 理解二维跳棋规则
2. `02-rules-3d-jump-chess.md` 理解三维跳棋规则
3. `03-geometry-model-a.md` 实现 A 模型
4. `04-geometry-model-b.md` 实现 B 模型
5. `05-configuration.md` 理解配置结构
6. `06-architecture.md` 理解整体架构
7. `07-action-representation.md` 理解动作与路径
8. `08-frontend-ui.md` 前端实现
9. `10-implementation-guide.md` 按步骤实现

参考资料中的开源项目主要用于对照规则和训练接口，不建议直接照搬二维代码到三维，因为几何和动作空间差异较大。
