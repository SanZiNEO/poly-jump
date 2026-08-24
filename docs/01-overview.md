# PolyJump 项目概览

## 定位

PolyJump 是一个可配置的三维跳棋游戏框架。

- 不是 AI 训练框架
- 提供完整可玩的游戏玩法
- 提供干净的后端/游戏环境接口
- 外部程序可以基于该接口运行自己的 AI、搜索或分析程序

## 技术栈

- 后端：Python 3.11+、FastAPI、Pydantic
- 前端：HTML + Three.js（CDN，无复杂构建）
- 测试：pytest

## 核心特性

- 多种几何模型
- 多种棋类玩法
- 可配置规则开关
- 积分制（前端可配置）
- AI 玩家 / 自动对弈
- 棋谱历史 / 回放
- 前端中英文切换
- 配置文件驱动
- 纯后端 headless 运行
- Hugging Face Docker 部署支持

## 仓库结构

```text
backend/
  app.py                 # FastAPI 入口
  game/
    config.py            # 配置类
    geometry/            # 所有几何模型
    moves/               # 移动生成/校验
    rules/               # 规则执行/吃子/胜负
    env.py               # 干净游戏环境接口
    scoring.py           # 积分制
    headless.py          # 纯后端运行入口
frontend/
  index.html
  menu.js
  main.js
  i18n.js
  ...
configs/                 # 配置示例
docs/                    # 当前文档
tests/                   # 测试
```

## 文档索引

| 文档 | 内容 |
|---|---|
| [02-geometry-models.md](./02-geometry-models.md) | 所有几何模型 |
| [03-game-rules.md](./03-game-rules.md) | 玩法规则 |
| [04-configuration.md](./04-configuration.md) | 配置 |
| [05-interfaces.md](./05-interfaces.md) | 后端/编程接口 |
| [06-frontend.md](./06-frontend.md) | 前端功能 |
| [07-ai-and-research.md](./07-ai-and-research.md) | AI/研究接口 |
| [08-references.md](./08-references.md) | 参考资料 |
