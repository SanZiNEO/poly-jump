# PolyJump

A configurable 3D jump-chess framework with A/B geometries and multi-player rule switches.

## 项目简介

PolyJump 是一个可配置的三维跳棋框架。

- 两套几何模型：
  - A 模型：XYZ 正方体 / 长方体网格
  - B 模型：FCC / 菱形十二面体风格点阵
- 一整套规则开关：
  - 移动方向 6 / 8 / 12 / 14 / 18 / 20 / 26
  - 玩家数 2 / 3 / 4 / 6 / 8
  - 普通移动 / 跳跃 / 连跳
  - 中国跳棋式自由停 / 国际跳棋式跳到底
  - 无吃子 / 西洋跳棋吃子 / 混合吃子
  - 金字塔 / 四棱锥初始布局
- 技术栈：
  - 后端：Python + FastAPI
  - 前端：HTML + Three.js
  - 可选小 AI：随机 / 贪心 / MCTS（后续可选）

## 文档

设计文档位于 [`docs/`](./docs/README.md)。

| 文档 | 内容 |
|---|---|
| 二维跳棋规则 | [docs/01-rules-2d-checkers.md](./docs/01-rules-2d-checkers.md) |
| 三维跳棋规则 | [docs/02-rules-3d-jump-chess.md](./docs/02-rules-3d-jump-chess.md) |
| A 模型几何 | [docs/03-geometry-model-a.md](./docs/03-geometry-model-a.md) |
| B 模型几何 | [docs/04-geometry-model-b.md](./docs/04-geometry-model-b.md) |
| 配置与开关 | [docs/05-configuration.md](./docs/05-configuration.md) |
| 项目架构 | [docs/06-architecture.md](./docs/06-architecture.md) |
| 动作表示 | [docs/07-action-representation.md](./docs/07-action-representation.md) |
| 前端界面 | [docs/08-frontend-ui.md](./docs/08-frontend-ui.md) |
| 可选小 AI | [docs/09-optional-ai.md](./docs/09-optional-ai.md) |
| 实现指南 | [docs/10-implementation-guide.md](./docs/10-implementation-guide.md) |
| 参考项目 | [docs/11-references.md](./docs/11-references.md) |

## 后端可编程接口

游戏规则引擎可以脱离前端单独运行，通过 JSON 配置启动：

```powershell
python -m backend.game.headless --config configs/a_2p_6dir.json --moves 10
```

示例配置位于 [`configs/`](./configs/)。

## License

See [LICENSE](./LICENSE).
