# PolyJump 设计文档

本目录是 PolyJump 的完整设计文档，按“可直接照着实现”的标准编写。

## 文档索引

| 文档 | 内容 |
|---|---|
| [01-rules-2d-checkers.md](./01-rules-2d-checkers.md) | 二维跳棋规则参考（中国跳棋 / 国际跳棋 / 变体） |
| [02-rules-3d-jump-chess.md](./02-rules-3d-jump-chess.md) | 三维跳棋规则总纲 |
| [03-geometry-model-a.md](./03-geometry-model-a.md) | A 模型：正方体 / 长方体几何 |
| [04-geometry-model-b.md](./04-geometry-model-b.md) | B 模型：FCC / 菱形十二面体几何 |
| [05-configuration.md](./05-configuration.md) | 所有可配置项与规则开关 |
| [06-architecture.md](./06-architecture.md) | 项目架构：后端 / 前端 / 数据流 |
| [07-action-representation.md](./07-action-representation.md) | 动作表示与合法路径生成 |
| [08-frontend-ui.md](./08-frontend-ui.md) | 前端界面与交互设计 |
| [09-optional-ai.md](./09-optional-ai.md) | 可选小 AI 实现（随机 / 贪心 / MCTS） |
| [10-implementation-guide.md](./10-implementation-guide.md) | 分步实现指南 |
| [11-references.md](./11-references.md) | 参考项目与资料链接 |
| [CURRENT.md](./CURRENT.md) | 当前实现状态：模型/玩法/接口/配置 |

## 核心概念

```
几何模型 Geometry
  ├── A：xyz 正交网格
  └── B：FCC 等步长点阵

棋盘 Board
  ├── 点集 valid_points
  ├── 玩家基地 base_regions
  └── 目标区 target_regions

配置 Config
  ├── geometry
  ├── board_size
  ├── direction_set
  ├── player_count
  ├── capture_mode
  ├── hop_mode
  └── ...

规则引擎 Rules
  ├── 合法移动生成
  ├── 大跳 / 连跳
  ├── 吃子 / 混合吃子
  └── 胜负判定

动作 Action
  └── 路径 Path = [起点, 中间点..., 终点]
```

## 设计原则

1. 所有规则都是配置项，不是硬编码。
2. 后端是权威规则引擎；前端只做展示和选择。
3. 动作统一用“路径”表示，覆盖一步 / 单跳 / 连跳。
4. A、B 两种几何共用同一个 `Board` / `Rules` / `Config` 接口。
5. 文档目标：让实现者不需要再问规则细节，直接照文档编码。
