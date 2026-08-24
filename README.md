# PolyJump

A configurable 3D jump-chess framework with multiple geometries, rule modes, scoring, replay, and clean programming interfaces.

> English version: [README.en.md](./README.en.md)

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
  - 中国跳棋 / 西洋跳棋 / 混合模式
  - 金字塔 / 四棱锥初始布局
- 技术栈：
  - 后端：Python + FastAPI
  - 前端：HTML + Three.js
  - 可选小 AI：随机 / 贪心 / MCTS（后续可选）

## 文档

设计文档位于 [`docs/`](./docs/README.md)。

| 文档 | 内容 |
|---|---|
| 项目概览 | [docs/01-overview.md](./docs/01-overview.md) |
| 几何模型 | [docs/02-geometry-models.md](./docs/02-geometry-models.md) |
| 游戏规则 | [docs/03-game-rules.md](./docs/03-game-rules.md) |
| 配置 | [docs/04-configuration.md](./docs/04-configuration.md) |
| 接口 | [docs/05-interfaces.md](./docs/05-interfaces.md) |
| 前端 | [docs/06-frontend.md](./docs/06-frontend.md) |
| AI / 研究 | [docs/07-ai-and-research.md](./docs/07-ai-and-research.md) |
| 参考资料 | [docs/08-references.md](./docs/08-references.md) |

## 后端可编程接口

游戏规则引擎可以脱离前端单独运行，通过 JSON 配置启动：

```powershell
python -m backend.game.headless --config configs/a_2p_6dir.json --moves 10
```

示例配置位于 [`configs/`](./configs/)。

## Hugging Face 部署

仓库已包含 Dockerfile，可直接部署为 HF Space：

1. 创建 Hugging Face Space，SDK 选择 **Docker**
2. 将本仓库推送到 Space
3. Space 默认启动：

```text
http://0.0.0.0:8000
```

Space 内只包含游戏本体，不包含 AI 训练内容。

## License

See [LICENSE](./LICENSE).
